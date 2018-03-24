from logging import getLogger

from src.reversi_zero.config import Config
from src.reversi_zero.lib.grpc_helper import FileServer

logger = getLogger(__name__)


def start(config: Config):
    FileServer(config).start()
