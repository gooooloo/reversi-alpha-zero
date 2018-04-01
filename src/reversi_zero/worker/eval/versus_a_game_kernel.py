import copy
import importlib
from logging import getLogger

from src.reversi_zero.config import Config
from src.reversi_zero.lib import ggf
from src.reversi_zero.lib.gtp_helper import GTPClient
from src.reversi_zero.lib.pipe_helper import PipeFilesManager
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

logger = getLogger(__name__)


def start(config: Config):
    return VersusPlayWorker(config).start()


class VersusPlayWorkerBase:
    def __init__(self, config: Config):
        self.config = config
        assert self.config.eval.n_games == 1
        assert len(self.config.ipc.pipe_pairs) == 3
        self.parent_pipe_pair = self.config.ipc.pipe_pairs[0]
        self.p1_pipe_pair = self.config.ipc.pipe_pairs[1]
        self.p2_pipe_pair = self.config.ipc.pipe_pairs[2]
        self.pipe_files = PipeFilesManager.new_one(self.config)
        self.p1_name = self.config.eval.p1_model_step
        self.p2_name = self.config.eval.p2_model_step

    def start_p1_server(self, gtp_pipe_pair):
        raise Exception('not implemented yet')

    def start_p2_server(self, gtp_pipe_pair):
        raise Exception('not implemented yet')

    def start(self):
        gtp_pipe_pairs = self.pipe_files.make_pipes(2)

        self.start_p1_server(gtp_pipe_pairs[0])
        self.start_p2_server(gtp_pipe_pairs[1])

        p1 = GTPClient(gtp_pipe_pairs[0].reverse_in_out())
        p2 = GTPClient(gtp_pipe_pairs[1].reverse_in_out())

        black, white = p1, p2
        black_name, white_name = self.p1_name, self.p2_name
        if not self.config.eval.p1_first:
            black, white = white, black
            black_name, white_name = white_name, black_name

        black.clear_board()
        white.clear_board()

        class_attr = getattr(importlib.import_module(self.config.env.env_module_name), self.config.env.env_class_name)
        env = class_attr()
        env.reset()

        ggf = env.new_ggf()
        ggf.set_black_name(black_name)
        ggf.set_white_name(white_name)

        next_is_black = True
        while True:
            if next_is_black:
                action = black.think()
                white.play(action)
                ggf.play(ggf.BLACK, action)
                env.step(action)
            else:
                action = white.think()
                black.play(action)
                ggf.play(ggf.WHITE, action)
                env.step(action)

            next_is_black = not next_is_black
            if env.done:
                break

        final_score = env.score
        ggf.set_final_score(final_score)

        if self.config.resource.eval_ggf_dir:
            ggf.write_to_file(self.config.resource.eval_ggf_dir)

        self.pipe_files.clear_pipes()

        black, white = [int(x) for x in final_score]

        if self.config.eval.p1_first:
            p1, p2 = black, white
        else:
            p1, p2 = white, black

        self.parent_pipe_pair.open_write_nonblock()
        self.parent_pipe_pair.write_int(p1)
        self.parent_pipe_pair.write_int(p2)
        self.parent_pipe_pair.close_write()


class VersusPlayWorker(VersusPlayWorkerBase):
    def __init__(self, config: Config):
        super().__init__(config)

    @staticmethod
    def start_gtp_server_process(pipe_pairs, config):
        cmd = build_child_cmd(type='gtp_server', opts=config.opts, pipe_pairs=pipe_pairs)
        return start_child_proc(cmd=cmd)

    def start_p1_server(self, gtp_pipe_pair):
        self.start_gtp_server_process([gtp_pipe_pair, self.p1_pipe_pair], self.config)

    def start_p2_server(self, gtp_pipe_pair):
        self.start_gtp_server_process([gtp_pipe_pair, self.p2_pipe_pair], self.config)

