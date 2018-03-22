import os
from logging import getLogger

from src.reversi_zero.agent.api import MODEL_SERVING_READY, MODEL_SERVING_START, MODEL_SERVING_STARTED
from src.reversi_zero.config import Config
from src.reversi_zero.lib.http import HttpPlayServer, HttpFileServer
from src.reversi_zero.lib.model_helpler import ask_model_dir
from src.reversi_zero.lib.pipe_helper import PipeFilesManager
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

logger = getLogger()


def start(config: Config):
    if config.opts.ask_model:
        model_dir = ask_model_dir(config)
        config.resource.model_config_path = os.path.join(model_dir, config.resource.model_config_filename)
        config.resource.model_weight_path = os.path.join(model_dir, config.resource.model_weight_filename)

    cmd = config.opts.cmd
    if cmd == 'http_server':
        return HTTPPlayServerWorker(config).start()
    elif cmd == 'http_fs':
        return HTTPModelFileServerWorker(config).start()
    else:
        raise Exception("error")


class HTTPPlayServerWorker:

    def __init__(self, config: Config):
        self.config = config
        assert not self.config.opts.pipe_pairs or len(self.config.opts.pipe_pairs) == 1

        self.parent_pipe_pair = self.config.opts.pipe_pairs[0] if self.config.opts.pipe_pairs else None
        self.pipe_files = PipeFilesManager.new_one(self.config)

    def start(self):
        pipe_pairs = self.pipe_files.make_pipes(3)
        pipe_pairs[0].open_read_nonblock()
        self.start_model_serving_process(self.config.resource.model_config_path,
                                         self.config.resource.model_weight_path,
                                         [pipe_pairs[0].reverse_in_out(), pipe_pairs[2]])
        x = pipe_pairs[0].read_int(allow_empty=False)
        assert x == MODEL_SERVING_READY
        pipe_pairs[0].open_write_nonblock()
        pipe_pairs[0].write_int(MODEL_SERVING_START)
        pipe_pairs[0].close_write()
        x = pipe_pairs[0].read_int(allow_empty=False)
        assert x == MODEL_SERVING_STARTED
        pipe_pairs[0].close_read()

        self.start_gtp_server_process([pipe_pairs[1].reverse_in_out(), pipe_pairs[2].reverse_in_out()])

        http_server = HttpPlayServer(pipe_pairs[1], self.config.opts.http_port)
        if self.parent_pipe_pair:
            self.parent_pipe_pair.open_write_nonblock()
            self.parent_pipe_pair.write('ready'.encode())
            self.parent_pipe_pair.close_write()
        http_server.start()

    def start_gtp_server_process(self, pipe_pairs):
        cmd = build_child_cmd(type='gtp_server', opts=self.config.opts, pipe_pairs=pipe_pairs)
        return start_child_proc(cmd=cmd, nocuda=True)

    def start_model_serving_process(self, model_config_path, model_weight_path, pipe_pairs):
        import copy
        opts = copy.copy(self.config.opts)
        opts.model_config_path = model_config_path
        opts.model_weight_path = model_weight_path

        cmd = build_child_cmd(type='model_serving', opts=opts, pipe_pairs=pipe_pairs)
        return start_child_proc(cmd=cmd)


class HTTPModelFileServerWorker:

    def __init__(self, config: Config):
        self.config = config

    def start(self):
        port = self.config.opts.http_port
        http_server = HttpFileServer(config=self.config, port=port)
        http_server.start()


class HTTPPlayDataFileServerWorker:

    def __init__(self, config: Config):
        self.config = config

    def start(self):
        folder = 'TODO'
        port = self.config.opts.http_port
        http_server = HttpFileServer(folder=folder, port=port)
        http_server.start()


class HTTPResFileServerWorker:

    def __init__(self, config: Config):
        self.config = config

    def start(self):
        folder = 'TODO'
        port = self.config.opts.http_port
        http_server = HttpFileServer(folder=folder, port=port)
        http_server.start()
