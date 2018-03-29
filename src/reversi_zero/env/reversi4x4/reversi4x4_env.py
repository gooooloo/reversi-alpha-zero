from logging import getLogger

from src.reversi_zero.env.reversi4x4.lib.reversi_generic_env import ReversiGenericEnv

logger = getLogger(__name__)


class Reversi4x4Env(ReversiGenericEnv):
    def __init__(self):
        super(Reversi4x4Env, self).__init__(edge_size=4, board_history_max_len=1)
