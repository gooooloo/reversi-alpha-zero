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
        self.cache_server = ModelCacheServer(self.config.opts.pipe_pairs[1:], self.config.model_cache.model_cache_size)

    def start(self):
        self.cache_server.get_ready()
        self.parent_pipe_pair.open_write_nonblock()
        self.parent_pipe_pair.write_int(1)  # means: I am ready
        self.parent_pipe_pair.close_write()
        self.cache_server.serve()

