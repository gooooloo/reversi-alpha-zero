from logging import getLogger

from src.reversi_zero.env.reversi4x4.lib.reversi_generic_env import ReversiGenericEnv

logger = getLogger(__name__)


class Reversi6x6Env(ReversiGenericEnv):
    def __init__(self):
        super(Reversi6x6Env, self).__init__(edge_size=6, board_history_max_len=2)
