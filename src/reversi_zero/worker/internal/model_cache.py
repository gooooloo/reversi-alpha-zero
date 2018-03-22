from logging import getLogger

from src.reversi_zero.agent.model_cache import ModelCacheServer
from src.reversi_zero.config import Config

logger = getLogger(__name__)


def start(config: Config):
    return ModelCacheWorker(config).start()


class ModelCacheWorker:
    def __init__(self, config: Config):
        self.config = config
        assert len(self.config.opts.pipe_pairs) > 1
        self.parent_pipe_pair = self.config.opts.pipe_pairs[0]
        self.data_pipe_pair = self.config.opts.pipe_pairs[1:]

    def start(self):
        cache_server = ModelCacheServer(self.parent_pipe_pair, self.data_pipe_pair, self.config.model_cache.model_cache_size)
        cache_server.serve()

