# -*- coding: utf-8 -*-

import numpy as np
import random

from logging import getLogger, INFO

import time

logger = getLogger(__name__)
logger.setLevel(INFO)


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


class TimedEvaluatePlayer(EvaluatePlayer):
    def __init__(self, time_strategy, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_strategy = time_strategy

    def think(self, tau=0):
        timeout = self.time_strategy.get_seconds_for_thinking()
        return self.game_tree.mcts_and_play(tau, timeout)

    def play(self, *args, **kwargs):
        self.time_strategy.play()
        return super().play(*args, **kwargs)


class GameTree(object):
    def __init__(self, make_sim_env_fn, config=None, play_config=None, api=None):
        self.make_sim_env_fn = make_sim_env_fn
        self.config = config
        self.play_config = play_config or self.config.play
        self.root_node = Node(self.play_config.c_puct)
        self.api = api

        self.allow_rotate_flip_ob = True
        self.virtual_loss = self.config.play.virtual_loss

    def expand_root(self, root_env):
        p, v = self.api.predict(np.asarray(root_env.observation))
        self.root_node.expand_and_evaluate(p, v, root_env.legal_moves)

    def mcts_and_play(self, tau, timeout=None):
        self.mcts(timeout)
        return self.play(tau)

    def keep_only_subtree(self, action):
        self.root_node = self.root_node.child_by_value(action)
        assert self.root_node is not None

    def mcts(self, timeout=None):
        # idea borrowed from https://github.com/tensorflow/minigo/blob/master/strategies.py

        assert self.root_node.expanded

        # Question: is it correct doing it every time mcts starts, or should it be just first step of a game?
        self.root_node.add_dirichlet_noise(self.play_config.noise_eps, self.play_config.dirichlet_alpha)

        deadline = time.time() + timeout if timeout else None

        nodes_to_sim = [] if timeout else [(self.root_node, None) for _ in range(self.play_config.simulation_num_per_move)]
        nodes_to_predict = []
        n_sim, n_cont_sim = 0, 0
        while True:
            if n_sim and deadline and time.time() >= deadline:
                break
            if n_sim and not deadline and not nodes_to_sim:
                break

            n_sim += 1

            nodes_to_sim = nodes_to_sim or [(self.root_node, None)]

            cur_node, env = nodes_to_sim.pop(0)
            env = env or self.make_sim_env_fn()

            while True:
                next_node = cur_node.select_best_child_and_add_virtual_loss(self.virtual_loss)
                env.step(next_node.value)

                if env.done:
                    v = -1 if env.last_player_wins else 1 if env.last_player_loses else 0
                    self.backup(next_node, v)
                    break

                if not next_node.expanded:
                    nodes_to_predict.append((next_node, env))
                    break

                cur_node = next_node

            if n_sim % self.play_config.prediction_queue_size == 0 and nodes_to_predict:
                nodes_not_backup = self.predict_and_backup(nodes_to_predict, always_backup=False)
                nodes_to_sim = nodes_not_backup + nodes_to_sim
                nodes_to_predict = []
                n_cont_sim += len(nodes_not_backup)

        # there maybe some unpredicted nodes
        if nodes_to_predict:
            self.predict_and_backup(nodes_to_predict, always_backup=True)

        # there maybe some ongoing nodes waiting to sim deeper
        for node,env in nodes_to_sim:
            if env:
                self.substract_virtual_loss(node)
                n_sim -= 1
                n_cont_sim -= 1

        logger.debug(f'think time: {timeout}; search times: {n_sim - n_cont_sim}')

    def predict_and_backup(self, node_envs, always_backup):
        ops = [random.randint(0, env.rotate_flip_op_count - 1)
               if self.allow_rotate_flip_ob and env.rotate_flip_op_count > 0
               else None
               for _,env in node_envs]

        data = np.asarray([env.observation if op is None else env.rotate_flip_ob(env.observation, op)
                           for (_,env),op in zip(node_envs, ops)])

        ps, vs = self.api.predict(data)

        nodes_not_backup = []
        for (node, env), p, v, op in zip(node_envs, ps, vs, ops):
            if op is not None:
                p = env.counter_rotate_flip_pi(p, op)
            if not node.expanded:
                node.expand_and_evaluate(p, v, env.legal_moves)
                self.backup(node, v)
            else:
                if always_backup:
                    self.backup(node, v)
                else:
                    nodes_not_backup.append((node, env))

        return nodes_not_backup

    def backup(self, leaf_node, v):
        cur_node = leaf_node
        while cur_node is not self.root_node:
            v = -v  # important: reverse v
            parent = cur_node.parent
            parent.backup_and_stubstract_virtual_loss(self.virtual_loss, v, cur_node.sibling_index)
            cur_node = parent

    def substract_virtual_loss(self, leaf_node):
        cur_node = leaf_node
        while cur_node is not self.root_node:
            parent = cur_node.parent
            parent.substract_virtual_loss(self.virtual_loss, cur_node.sibling_index)
            cur_node = parent

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

