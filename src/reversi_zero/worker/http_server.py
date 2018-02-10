import os
from logging import getLogger

from src.reversi_zero.config import Config
from src.reversi_zero.lib.http import HttpServer
from src.reversi_zero.lib.model_helpler import ask_model_dir
from src.reversi_zero.lib.pipe_helper import PipeFilesManager
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

logger = getLogger()


def start(config: Config):
    if config.opts.ask_model:
        model_dir = ask_model_dir(config)
        config.resource.model_config_path = os.path.join(model_dir, config.resource.model_config_filename)
        config.resource.model_weight_path = os.path.join(model_dir, config.resource.model_weight_filename)
    return HTTPServerWorker(config).start()


class HTTPServerWorker:

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
        pipe_pairs[0].read_no_empty(99, sleep_retry=0.1)  # having response means 'ready', whatever it is.
        pipe_pairs[0].close_read()

        self.start_gtp_server_process([pipe_pairs[1].reverse_in_out(), pipe_pairs[2].reverse_in_out()])

        http_server = HttpServer(pipe_pairs[1], self.config.opts.http_port)
        if self.parent_pipe_pair:
            self.parent_pipe_pair.open_write_nonblock()
            self.parent_pipe_pair.write('ready'.encode())
            self.parent_pipe_pair.close_write()
        http_server.start()

    def start_gtp_server_process(self, pipe_pairs):
        cmd = build_child_cmd(type='gtp_server', config=self.config, pipe_pairs=pipe_pairs)
        return start_child_proc(cmd=cmd, nocuda=True)

    def start_model_serving_process(self, model_config_path, model_weight_path, pipe_pairs):
        cmd = build_child_cmd(type='model_serving', config=self.config, pipe_pairs=pipe_pairs)
        cmd.extend([
            '--model-config-path', model_config_path,
            '--model-weight-path', model_weight_path,
        ])
        return start_child_proc(cmd=cmd)
