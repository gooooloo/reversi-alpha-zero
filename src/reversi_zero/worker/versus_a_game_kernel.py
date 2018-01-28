from logging import getLogger

import copy

from src.reversi_zero.config import Config
from src.reversi_zero.lib import gtp
from src.reversi_zero.lib.ggf import GGF
from src.reversi_zero.lib.gtp import GTPClient
from src.reversi_zero.lib.pipe_helper import PipeFilesManager
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

logger = getLogger(__name__)


def start(config: Config):
    return VersusPlayWorker(config).start()


class VersusPlayWorkerBase:
    def __init__(self, config: Config):
        self.config = config
        assert self.config.opts.n_games == 1
        assert len(self.config.opts.pipe_pairs) == 3
        self.parent_pipe_pair = self.config.opts.pipe_pairs[0]
        self.p1_pipe_pair = self.config.opts.pipe_pairs[1]
        self.p2_pipe_pair = self.config.opts.pipe_pairs[2]
        self.pipe_files = PipeFilesManager.new_one(self.config)
        self.p1_name = self.config.opts.p1_name
        self.p2_name = self.config.opts.p2_name

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
        if not self.config.opts.p1_first:
            black, white = white, black
            black_name, white_name = white_name, black_name

        black.clear_board()
        white.clear_board()

        ggf = GGF(black_name=black_name, white_name=white_name)
        next_is_black = True
        while True:
            if next_is_black:
                vertex = black.genmove(gtp.BLACK)
                white.play(gtp.BLACK, vertex)
                ggf.play(gtp.BLACK, vertex)
            else:
                vertex = white.genmove(gtp.WHITE)
                black.play(gtp.WHITE, vertex)
                ggf.play(gtp.WHITE, vertex)

            next_is_black = not next_is_black
            over = p1.is_over()
            if over:
                break

        final_score = p1.final_score()

        if self.config.opts.save_versus_dir:
            ggf.write_to_file(self.config.opts.save_versus_dir)

        self.pipe_files.clear_pipes()

        black, white = final_score

        if self.config.opts.p1_first:
            p1, p2 = black, white
        else:
            p1, p2 = white, black

        if p1 > p2:
            final_score = 'win'
        elif p1 < p2:
            final_score = 'lose'
        else:
            final_score = 'draw'
        self.parent_pipe_pair.write_nonblock(f'{final_score}'.encode())


class VersusPlayWorker(VersusPlayWorkerBase):
    def __init__(self, config: Config):
        super().__init__(config)

    @staticmethod
    def start_gtp_server_process(pipe_pairs, config):
        cmd = build_child_cmd(type='gtp_server', config=config, pipe_pairs=pipe_pairs)
        return start_child_proc(cmd=cmd, nocuda=True)

    def start_p1_server(self, gtp_pipe_pair):
        if self.config.opts.p1_n_sims is not None:
            p1_config = copy.copy(self.config)
            p1_config.play.simulation_num_per_move = self.config.opts.p1_n_sims
        else:
            p1_config = self.config
        self.start_gtp_server_process([gtp_pipe_pair, self.p1_pipe_pair], p1_config)

    def start_p2_server(self, gtp_pipe_pair):
        if self.config.opts.p2_n_sims is not None:
            p2_config = copy.copy(self.config)
            p2_config.play.simulation_num_per_move = self.config.opts.p2_n_sims
        else:
            p2_config = self.config
        self.start_gtp_server_process([gtp_pipe_pair, self.p2_pipe_pair], p2_config)

