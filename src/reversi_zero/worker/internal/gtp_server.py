import importlib
from logging import getLogger

import time

from src.reversi_zero.agent.api import ReversiModelAPIProxy
from src.reversi_zero.agent.player import EvaluatePlayer, TimedEvaluatePlayer
from src.reversi_zero.config import Config, EloConfig
from src.reversi_zero.gtp.reversi_gtp import ReversiGTPServer
from src.reversi_zero.lib import gtp
from src.reversi_zero.lib.time_strategy import TimeStrategy

logger = getLogger()


def start(config: Config):
    EloConfig().update_play_config(config.play)
    return GTPServerWorker(config).start()


class GTPServerWorker:
    def __init__(self, config: Config):
        self.config = config
        assert len(self.config.opts.pipe_pairs) in [1, 2]
        self.parent_pipe_pair = self.config.opts.pipe_pairs[0]
        self.model_pipe_pair = self.config.opts.pipe_pairs[1] if len(self.config.opts.pipe_pairs) == 2 else None

        # TODO: use arguments
        self.config.play.noise_eps = 0
        self.config.play.change_tau_turn = 0

        self.gtp_server = None

    def start(self):
        game_obj = self.get_game_obj()
        self.gtp_server = ReversiGTPServer(game_obj)

        self.parent_pipe_pair.open_read_nonblock()
        while True:
            cmd = self.parent_pipe_pair.read_no_empty(sleep_retry=0.1)
            result = self.gtp_server.cmd(cmd.decode())
            self.parent_pipe_pair.open_write_block()
            self.parent_pipe_pair.write(result.encode())
            self.parent_pipe_pair.close_write()

    def get_game_obj(self):
        assert self.model_pipe_pair
        return GTPGameObj(self.config, self.model_pipe_pair)


class GTPGameObj(object):
    def __init__(self, config, model_pipe_pair):
        self.size = config.env.board_edge_size
        self.pass_action = self.size * self.size
        self.pass_vertex = gtp.PASS
        self.config = config
        self.env = None
        self.player = None
        self.api = ReversiModelAPIProxy(self.config, model_pipe_pair)

        self.clear()

    def v_2_a(self, vertex):
        if vertex == self.pass_vertex:
            return self.pass_action
        (x, y) = vertex
        return (x - 1) * self.size + (y - 1)

    def a_2_v(self, action):
        if action == self.pass_action:
            return self.pass_vertex
        return action // self.size + 1, action % self.size + 1

    def clear(self):
        class_attr = getattr(importlib.import_module(self.config.env.env_module_name), self.config.env.env_class_name)
        self.env = class_attr()
        self.env.reset()

        def make_sim_env_fn():
            return self.env.copy()

        if self.config.opts.n_minutes:
            time_strategy = TimeStrategy(minutes_per_game=self.config.opts.n_minutes,
                                         whole_move_num=self.config.time.whole_move_num,
                                         endgame_move_num=self.config.time.endgame_move_num,
                                         decay_factor=self.config.time.decay_factor)
            self.player = TimedEvaluatePlayer(time_strategy=time_strategy,
                                              make_sim_env_fn=make_sim_env_fn, config=self.config, api=self.api)
        else:
            self.player = EvaluatePlayer(make_sim_env_fn=make_sim_env_fn, config=self.config, api=self.api)
        self.player.prepare(self.env)

    def make_move(self, color, vertex):
        action = self.v_2_a(vertex)
        self.env.step(action)
        self.player.play(action, self.env)

        return True

    def get_move(self, color):
        action, _, _ = self.player.think()
        return self.a_2_v(action)

    def is_over(self):
        return self.env.done

    def final_score(self):
        return self.env.score
