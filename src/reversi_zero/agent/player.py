# -*- coding: utf-8 -*-

import numpy as np
import random

from asyncio.queues import Queue
from collections import namedtuple
from logging import getLogger, WARNING
import asyncio


getLogger('asyncio').setLevel(WARNING)
logger = getLogger(__name__)

QueueItem = namedtuple("QueueItem", "node state future")


class SelfPlayer(object):
    def __init__(self, make_sim_env_fn, config, api, play_config=None):
        self.game_tree = GameTree(make_sim_env_fn=make_sim_env_fn, config=config, api=api, play_config=play_config)

    def prepare(self, root_env):
        self.game_tree.expand_root(root_env=root_env)

    def think(self, tau=0):
        return self.game_tree.mcts_and_play(tau)

    def play(self, act):
        self.game_tree.keep_only_subtree(act)


class EvaluatePlayer(SelfPlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Before the model becomes accurate, rotate_flip introduces randomness.
        self.game_tree.allow_rotate_flip_ob = False

    def play(self, act, env):
        self.game_tree.keep_only_subtree(act)
        if not self.game_tree.root_node.expanded:
            # possible that opposite plays an action which I haven't searched yet.
            self.game_tree.expand_root(root_env=env)

    def get_think_info(self):
        node = self.game_tree.root_node
        return node.full_N, node.full_Q, node.full_combined_V, node.full_P


class GameTree(object):
    def __init__(self, make_sim_env_fn, config=None, play_config=None, api=None):
        self.make_sim_env_fn = make_sim_env_fn
        self.config = config
        self.play_config = play_config or self.config.play
        self.root_node = Node(self.play_config.c_puct)
        self.prediction_queue = Queue(self.play_config.prediction_queue_size)
        self.sem = asyncio.Semaphore(self.play_config.parallel_search_num)
        self.api = api

        self.loop = asyncio.get_event_loop()
        self.running_simulation_num = 0

        self.allow_rotate_flip_ob = True

    def expand_root(self, root_env):
        p, v = self.api.predict(np.asarray(root_env.observation))
        self.root_node.expand_and_evaluate(p, v, root_env.legal_moves)

    def mcts_and_play(self, tau):
        self.mcts()
        return self.play(tau)

    def keep_only_subtree(self, action):
        self.root_node = self.root_node.child_by_value(action)
        assert self.root_node is not None

    def mcts(self):

        # Question: is it correct doing it every time mcts starts, or should it be just first step of a game?
        self.root_node.add_dirichlet_noise(self.play_config.noise_eps, self.play_config.dirichlet_alpha)

        self.running_simulation_num = 0
        coroutine_list = []
        for it in range(self.play_config.simulation_num_per_move):
            coroutine_list.append(self.simulate())
        coroutine_list.append(self.prediction_worker())
        self.loop.run_until_complete(asyncio.gather(*coroutine_list))

    async def simulate(self):
        self.running_simulation_num += 1
        with await self.sem:
            leaf_v = await self.simulate_internal()
            self.running_simulation_num -= 1
            return leaf_v

    async def simulate_internal(self):
        assert self.root_node.expanded

        virtual_loss = self.config.play.virtual_loss
        env = self.make_sim_env_fn()
        leaf_node = None
        leaf_v = None

        cur_node = self.root_node

        while leaf_node is None:

            next_node = await cur_node.select_best_child_and_add_virtual_loss_lock(virtual_loss)

            env.step(next_node.value)
            if env.done:
                leaf_node = next_node
                leaf_v = -1 if env.last_player_wins else 1 if env.last_player_loses else 0
                break

            if not next_node.expanded and not await next_node.expanded_lock():
                v, new = await self.expand_and_evaluate(env, next_node)
                if new:
                    leaf_node = next_node
                    leaf_v = v
                    break

            cur_node = next_node

        assert leaf_node is not None
        assert leaf_v is not None

        v = leaf_v

        # backup
        cur_node = leaf_node
        while cur_node is not self.root_node:
            v = -v  # important: reverse v

            parent = cur_node.parent
            await parent.backup_and_substract_virtual_loss_lock(virtual_loss, v, cur_node.sibling_index)

            cur_node = parent

        return -v  # v for root node

    async def expand_and_evaluate(self, env, node):

        # do it outside of synchronized block to cut down synchronization overhead.
        ob, rotate_flip_op = np.asarray(env.observation), None
        if self.allow_rotate_flip_ob and env.rotate_flip_op_count > 0:
            rotate_flip_op = random.randint(0, env.rotate_flip_op_count - 1)
            ob = env.rotate_flip_ob(ob, rotate_flip_op)

        async def gen_v_future_coroutine():
            the_future = await self.predict(ob)
            return (the_future, rotate_flip_op)

        # this will overwrite previous rotate_flip_op, it is ok.
        (future, rotate_flip_op), new = await node.v_future_lock(gen_v_future_coroutine)

        await future
        p, v = future.result()

        if rotate_flip_op is not None:
            p = env.counter_rotate_flip_pi(p, rotate_flip_op)

        await node.expand_and_evaluate_lock(p, v, env.legal_moves)

        return float(v), new

    async def prediction_worker(self):
        margin = 10
        q = self.prediction_queue
        while self.running_simulation_num > 0 or margin > 0:
            if q.empty():
                margin -= 1 if margin > 0 else 0
                await asyncio.sleep(self.config.play.prediction_worker_sleep_sec)
                continue
            item_list = [q.get_nowait() for _ in range(q.qsize())]
            data = np.array([x.state for x in item_list])
            policy_ary, value_ary = self.api.predict(data)  # policy_ary: [n, 64], value_ary: [n, 1]
            for p, v, item in zip(policy_ary, value_ary, item_list):
                item.future.set_result((p, v))

    async def predict(self, x):
        future = self.loop.create_future()
        item = QueueItem(self, x, future)
        await self.prediction_queue.put(item)
        return future

    # those illegal actions are with full_N == 0, so won't be played
    def play(self, tau):
        N = self.root_node.full_N
        if abs(tau-1) < 1e-10:
            pi = N / np.sum(N)
            act = np.random.choice(range(len(pi)), p=pi)
            assert pi[act] > 0
        else:
            assert abs(tau) < 1e-10, f'tau={tau}(expected to be either 0 or 1 only)'
            act = random.choice(np.argwhere(abs(N - np.amax(N)) < 1e-10).flatten().tolist())
            pi = np.zeros([len(N)])
            pi[act] = 1

        # the paper says, AGZ resigns if both root value and best child value are lower than threshold
        # TODO: is it v or Q or Q+U to check?
        root_v = self.root_node.v
        # child'v is opponent's winning rate, need to reverse
        # Note that root_node.children are only for those legal action.
        children_v = [-child.v for child in self.root_node.children]
        if len(children_v) > 0:
            best_child_v = np.max(children_v)
        else:
            best_child_v = root_v  # trick. Since it is for resign_check only, it works to let be root_v.
        values_of_resign_check = (root_v, best_child_v)

        return int(act), pi, values_of_resign_check


class Node(object):
    def __init__(self, c_puct, parent=None, sibling_index=None, value=None):
        self.children = None
        self._parent = parent

        self._c_puct = c_puct
        self._sibling_index = sibling_index
        self._value = value  # corresponding "action" of env

        self.p = None
        self.W = None
        self.Q = None
        self.N = None
        self.v = 0.

        self.lock = asyncio.Lock()

        self.v_future = None

        # below variables are only for speeding up MCTS
        self._sum_n = None
        self._best_children_indices = None
        self._full_n_size = None

    # given the real meaning of node.value, full_N is actually N for every "action" of env
    @property
    def full_N(self):
        assert self.expanded

        assert np.sum(self.N) > 0, f'full_N is called with self.N={self.N}'

        ret = np.zeros([self._full_n_size])
        for node in self.children:
            ret[node.value] = self.N[node.sibling_index]

        assert abs(np.sum(self.N) - np.sum(ret)) < 1e-10
        return ret

    # given the real meaning of node.value, full_P is actually P for every "action" of env
    @property
    def full_P(self):
        assert self.expanded

        ret = np.zeros([self._full_n_size])
        for node in self.children:
            ret[node.value] = self.p[node.sibling_index]

        assert abs(np.sum(self.p) - np.sum(ret)) < 1e-10
        return ret

    # given the real meaning of node.value, full_Q is actually Q for every "action" of env
    @property
    def full_Q(self):
        assert self.expanded

        ret = np.zeros([self._full_n_size])
        for node in self.children:
            ret[node.value] = self.Q[node.sibling_index]

        assert abs(np.sum(self.Q) - np.sum(ret)) < 1e-10
        return ret

    # given the real meaning of node.value, full_combined_V is actually combined_V for every "action" of env
    @property
    def full_combined_V(self):
        assert self.expanded

        v = self._children_v()
        ret = np.zeros([self._full_n_size])
        for node in self.children:
            ret[node.value] = v[node.sibling_index]

        assert abs(np.sum(v) - np.sum(ret)) < 1e-10
        return ret

    @property
    def expanded(self):
        return self.children is not None

    @property
    def value(self):
        return self._value

    @property
    def sibling_index(self):
        return self._sibling_index

    @property
    def parent(self):
        return self._parent

    def child_by_value(self, value):
        return next((child for child in self.children if child.value == value), None)

    def expand_and_evaluate(self, p, v, legal_moves):

        if self.expanded:
            return

        self.p = p[legal_moves == 1]  # this.p is (typically much) shorter than p
        assert 0 < len(self.p) < len(legal_moves), f'{len(self.p)}, {len(legal_moves)} '

        self.v = v
        self.W = np.zeros([len(self.p)])
        self.Q = np.zeros([len(self.p)])
        self.N = np.zeros([len(self.p)])

        actions = (i for i,v in enumerate(legal_moves) if v == 1)
        self.children = [Node(c_puct=self._c_puct, parent=self, sibling_index=i, value=a)
                         for i,a in enumerate(actions)]
        assert len(self.children) > 0

        self._sum_n = 0
        self._best_children_indices = None
        self._full_n_size = len(legal_moves)

    def add_dirichlet_noise(self, eps, alpha):
        self.p = (1-eps)*self.p + eps*np.random.dirichlet([alpha]*len(self.p))
        self._best_children_indices = None

    def add_virtual_loss(self, virtual_loss, child):
        self.N[child] += virtual_loss
        self.W[child] -= virtual_loss
        self.Q[child] = self.W[child] / self.N[child]
        assert self.N[child] > 0, f'N[{child}]={self.N[child]}'

        self._sum_n += virtual_loss
        self._best_children_indices = None

    def substract_virtual_loss(self, virtual_loss, child):
        self.N[child] -= virtual_loss
        self.W[child] += virtual_loss
        self.Q[child] = self.W[child] / self.N[child] if self.N[child] > 1e-5 else 0
        assert self.N[child] >= 0, f'N[{child}]={self.N[child]}'

        self._sum_n -= virtual_loss
        self._best_children_indices = None

    def backup(self, v, child):
        self.N[child] += 1
        self.W[child] += v
        self.Q[child] = self.W[child] / self.N[child]
        assert self.N[child] > 0, f'N[{child}]={self.N[child]}'

        self._sum_n += 1
        self._best_children_indices = None

    def backup_and_stubstract_virtual_loss(self, virtual_loss, v, child):
        self.backup(v, child)
        self.substract_virtual_loss(virtual_loss, child)

    def best_children_indices(self):
        if self._best_children_indices is None:
            if len(self.p) == 1:
                self._best_children_indices = [0]
            else:
                v = self._children_v()
                self._best_children_indices = np.argwhere(abs(v-np.amax(v)) < 1e-10).flatten().tolist()

        return self._best_children_indices

    def _children_v(self):
        sqrt_sum_n = np.sqrt(self._sum_n)
        return self.Q + self._c_puct * self.p * sqrt_sum_n / (1 + self.N)

    def select_best_child_and_add_virtual_loss(self, virtual_loss):
        ci = random.choice(self.best_children_indices())
        next_node = self.children[ci]
        self.add_virtual_loss(virtual_loss, next_node.sibling_index)

        return next_node

    async def expanded_lock(self):
        with await self.lock:
            return self.expanded

    async def expand_and_evaluate_lock(self, *args, **kwargs):
        with await self.lock:
            return self.expand_and_evaluate(*args, **kwargs)

    async def select_best_child_and_add_virtual_loss_lock(self, *args, **kwargs):
        with await self.lock:
            return self.select_best_child_and_add_virtual_loss(*args, **kwargs)

    async def backup_and_substract_virtual_loss_lock(self, *args, **kwargs):
        with await self.lock:
            return self.backup_and_stubstract_virtual_loss(*args, **kwargs)

    async def v_future_lock(self, gen_v_future_coroutine):
        with await self.lock:
            new = False
            if not self.v_future:
                self.v_future = await gen_v_future_coroutine()
                new = True
            return self.v_future, new

