import importlib
from logging import getLogger
from random import random
from time import time
import numpy as np

from src.reversi_zero.agent.api import ReversiModelAPIProxy
from src.reversi_zero.agent.player import SelfPlayer
from src.reversi_zero.config import Config
from src.reversi_zero.lib.data_helper import remove_old_play_data, save_play_data
from src.reversi_zero.lib.resign_helper import load_resign_v, ResignCtrl, report_resign_ctrl

logger = getLogger(__name__)


def start(config: Config):
    return SelfPlayWorker(config).start()


class SelfPlayWorker:
    def __init__(self, config: Config):
        self.config = config
        assert self.config.opts.pipe_pairs
        assert len(self.config.opts.pipe_pairs) == 1
        self.pipe_pair = self.config.opts.pipe_pairs[0]
        self.api = ReversiModelAPIProxy(self.config, self.pipe_pair)

    def start(self):

        buffer = []
        game_idx = 1

        resign_ctrl = ResignCtrl()
        loaded_v = load_resign_v(self.config)
        resign_v = self.config.play.v_resign_init if loaded_v is None else loaded_v

        logger.debug("game is on!!!")
        while True:
            start_time = time()

            prop = self.config.play.v_resign_disable_prop
            should_resign = random() >= prop if self.config.play.can_resign else False
            moves, resign_ctrl_tmp = self.play_a_game(should_resign, resign_v)
            buffer += moves
            resign_ctrl += resign_ctrl_tmp

            end_time = time()
            logger.debug(f"play game {game_idx} time={end_time - start_time} sec")

            if (game_idx % self.config.play_data.nb_game_in_file) == 0:
                save_play_data(self.config, buffer)
                buffer = []
                remove_old_play_data(self.config)

                report_resign_ctrl(self.config, resign_ctrl)
                resign_ctrl = ResignCtrl()
                loaded_v = load_resign_v(self.config)
                resign_v = resign_v if loaded_v is None else loaded_v

            game_idx += 1
            if game_idx > self.config.opts.n_games:
                break

    def play_a_game(self, should_resign, v_resign):
        class_attr = getattr(importlib.import_module(self.config.env.env_module_name), self.config.env.env_class_name)
        env = class_attr()
        env.reset()

        def make_sim_env_fn():
            return env.copy()

        player = SelfPlayer(make_sim_env_fn=make_sim_env_fn, config=self.config, api=self.api)
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

            moves += [[env.compress_ob(env.observation).tolist(), np.asarray(pi).tolist()]]

            env.step(act)
            player.play(act)

            if self.config.play.render:
                env.render()

        if env.black_wins:
            z = 1
        elif env.black_loses:
            z = -1
        else:
            z = 0
        for i, move in enumerate(moves):
            move += [z if i%2==0 else -z]

        if resign_predicted_winner is not None:
            f_p_n = 0 if resign_predicted_winner == env.winner else 1
            resign_ctrl = ResignCtrl(1, f_p_n)
        else:
            resign_ctrl = ResignCtrl()

        return moves, resign_ctrl

