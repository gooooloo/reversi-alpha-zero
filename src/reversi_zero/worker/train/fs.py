
from logging import getLogger

from src.reversi_zero.config import Config
from src.reversi_zero.lib.resign_helper import keep_updating_resign_ctrl

logger = getLogger(__name__)


def start(config: Config):
    return ResignationWorker(config).start()


class ResignationWorker:
    def __init__(self, config: Config):
        self.config = config

    def start(self):
        keep_updating_resign_ctrl(self.config)
