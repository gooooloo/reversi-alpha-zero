import importlib
from logging import getLogger
from time import time

import numpy as np

from src.reversi_zero.agent.api import ReversiModelAPIProxy
from src.reversi_zero.agent.model_cache import ModelCacheClient
from src.reversi_zero.agent.player import SelfPlayer
from src.reversi_zero.config import Config
from src.reversi_zero.lib.chunk_pb2 import ResignFalsePositive, Move
from src.reversi_zero.lib.grpc_helper import GrpcClient

logger = getLogger(__name__)


def start(config: Config):
    return SelfPlayWorker(config).start()


class SelfPlayWorker:
    def __init__(self, config: Config):
        self.config = config
        assert self.config.opts.pipe_pairs
        assert len(self.config.opts.pipe_pairs) in (1, 2)
        self.api_pipe_pair = self.config.opts.pipe_pairs[0]
        self.api = ReversiModelAPIProxy(self.config, self.api_pipe_pair)
        self.grpc_client = GrpcClient(self.config)

        if len(self.config.opts.pipe_pairs) > 1:
            self.cache_pipe_pair = self.config.opts.pipe_pairs[1]
            self.model_cache = ModelCacheClient(self.cache_pipe_pair)
        else:
            self.model_cache = None

    def start(self):
        for game_idx in range(self.config.opts.n_games):
            start_time = time()

            resign_v = self.grpc_client.ask_resign_v()

            moves, resign_fp = self.play_a_game(resign_v)

            end_time = time()
            logger.debug(f"eval game {game_idx} time={end_time - start_time} sec")

            self.grpc_client.upload_play_data(iter(moves))

            if resign_fp.n > 0:
                self.grpc_client.report_resign_false_positive(resign_fp)

    def play_a_game(self, resign_v):
        class_attr = getattr(importlib.import_module(self.config.env.env_module_name), self.config.env.env_class_name)
        env = class_attr()
        env.reset()

        def make_sim_env_fn():
            return env.copy()

        player = SelfPlayer(make_sim_env_fn=make_sim_env_fn, config=self.config, api=self.api, model_cache=self.model_cache)
        player.prepare(root_env=env)

        moves = []
        resign_predicted_winner = None

        while not env.done:
            tau = 1 if env.turn < self.config.play.change_tau_turn else 0
            act, pi, vs = player.think(tau)

            if all(v < resign_v.v for v in vs):
                if resign_v.should_resign:
                    env.resign()
                    break
                if resign_predicted_winner is None:
                    resign_predicted_winner = env.last_player

            moves.append(Move(cob=np.asarray(env.compress_ob(env.observation), dtype=env.cob_dtype).tobytes(),
                              pi=np.asarray(pi, dtype=np.float32).tobytes(),
                              z=0))

            env.step(act)
            player.play(act)

        if env.black_wins:
            z = 1
        elif env.black_loses:
            z = -1
        else:
            z = 0
        for i, move in enumerate(moves):
            move.z = z

        if resign_predicted_winner is not None:
            f_p_n = 0 if resign_predicted_winner == env.winner else 1
            resign_fp = ResignFalsePositive(n=1, f_p_n=f_p_n)
        else:
            resign_fp = ResignFalsePositive(n=0, f_p_n=0)

        return moves, resign_fp

