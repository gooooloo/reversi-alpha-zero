import importlib
from logging import getLogger
from time import time

import numpy as np

from src.reversi_zero.agent.api import ReversiModelAPIProxy
from src.reversi_zero.agent.model_cache import ModelCacheClient
from src.reversi_zero.agent.player import SelfPlayer
from src.reversi_zero.config import Config
from src.reversi_zero.lib import chunk_pb2
from src.reversi_zero.lib.grpc_helper import FileClient
from src.reversi_zero.lib.resign_helper import ResignCtrl

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

        if len(self.config.opts.pipe_pairs) > 1:
            self.cache_pipe_pair = self.config.opts.pipe_pairs[1]
            self.model_cache = ModelCacheClient(self.cache_pipe_pair)
        else:
            self.model_cache = None

    def start(self):

        game_idx = 1

        file_client = FileClient(self.config)

        logger.debug("game is on!!!")
        while True:
            start_time = time()

            thres = file_client.ask_resign_threshold()
            should_resign, resign_v = thres.enabled, thres.v

            moves, resign_ctrl = self.play_a_game(should_resign, resign_v)

            end_time = time()
            logger.debug(f"play game {game_idx} time={end_time - start_time} sec")

            file_client.upload_play_data(moves)

            if resign_ctrl.n > 0:
                file_client.report_resign_ctrl(resign_ctrl)

            game_idx += 1
            if game_idx > self.config.opts.n_games:
                break

    def play_a_game(self, should_resign, v_resign):
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

            if all(v < v_resign for v in vs):
                if should_resign:
                    # logger.debug(f'Resign: v={vs[0]:.4f}, child_v={vs[1]:.4f}, thres={v_resign:.4f}')
                    env.resign()
                    break
                if resign_predicted_winner is None:
                    resign_predicted_winner = env.last_player

            moves.append(chunk_pb2.Move(cob=env.compress_ob(env.observation).tobytes(), pi=np.asarray(pi).tobytes(), z=0))

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
            resign_ctrl = ResignCtrl(1, f_p_n)
        else:
            resign_ctrl = ResignCtrl(0, 0)

        return moves, resign_ctrl

