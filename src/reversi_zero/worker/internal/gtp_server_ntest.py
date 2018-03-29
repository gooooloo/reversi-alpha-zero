import os
from logging import getLogger, WARNING

from src.reversi_zero.config import Config, EloConfig
from src.reversi_zero.env.reversi.lib.nboard import GTPNBoardGameObj
from src.reversi_zero.worker.internal.gtp_server import GTPServerWorker

logger = getLogger()
logger.setLevel(WARNING)


def start(config: Config):
    EloConfig().update_play_config(config.play)
    return GTPNTestServerWorker(config).start()


class GTPNTestServerWorker(GTPServerWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_game_obj(self):
        return GTPNTestGameObj(self.config)


class GTPNTestGameObj(GTPNBoardGameObj):
    def __init__(self, config):
        assert 'NTEST_HOME' in os.environ
        ntest_home = os.environ['NTEST_HOME']
        ntest_name = 'ntest'  # on OSX it should be mNTest, on Windows... I don't know
        depth = config.opts.ntest_depth
        super().__init__(cmd=ntest_name, cwd=ntest_home, depth=depth)
