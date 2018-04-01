import copy
import importlib
from logging import getLogger

from src.reversi_zero.agent.api import ReversiModelAPIProxy
from src.reversi_zero.agent.player import EvaluatePlayer
from src.reversi_zero.config import Config, EloConfig
from src.reversi_zero.lib.gtp_helper import GTPServer

logger = getLogger()


def start(config: Config):
    EloConfig().update_play_config(config.play)
    return GTPServerWorker(config).start()


class GTPServerWorker:
    def __init__(self, config: Config):
        config = copy.copy(config)
        assert len(config.ipc.pipe_pairs) in [1, 2]

        parent_pipe_pair = config.ipc.pipe_pairs[0]
        model_pipe_pair = config.ipc.pipe_pairs[1] if len(config.ipc.pipe_pairs) == 2 else None

        config.play.noise_eps = 0
        config.play.change_tau_turn = 0

        api = ReversiModelAPIProxy(config, model_pipe_pair)

        class_attr = getattr(importlib.import_module(config.env.env_module_name), config.env.env_class_name)
        env = class_attr()
        env.reset()

        def make_sim_env_fn():
            return env.copy()
        player = EvaluatePlayer(make_sim_env_fn=make_sim_env_fn, config=config, api=api)

        self.gtp_server = GTPServer(env=env, player=player, pipe_pair=parent_pipe_pair)

    def start(self):
        self.gtp_server.start()
