from logging import getLogger

from src.reversi_zero.agent.api import ReversiModelAPIServer
from src.reversi_zero.config import Config
from src.reversi_zero.lib import tf_util

logger = getLogger(__name__)


def start(config: Config):
    if config.opts.gpu_mem_frac is not None:
        tf_util.set_session_config(per_process_gpu_memory_fraction=config.opts.gpu_mem_frac)
    return ModelServingWorker(config).start()


class ModelServingWorker:
    def __init__(self, config):
        self.config = config
        assert len(self.config.opts.pipe_pairs) > 1
        self.parent_pipe_pair = self.config.opts.pipe_pairs[0]
        self.data_pipe_pair = self.config.opts.pipe_pairs[1:]

    def start(self):
        api = ReversiModelAPIServer(self.config, self.parent_pipe_pair, self.data_pipe_pair)
        api.start()
