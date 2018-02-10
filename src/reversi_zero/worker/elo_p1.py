from logging import getLogger

from src.reversi_zero.config import Config
from src.reversi_zero.lib import elo as elo_lib
from src.reversi_zero.lib.pipe_helper import PipeFilesManager, reverse_in_out
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

logger = getLogger(__name__)


def start(config):
    return EloWorker(config).start()


class EloWorkerBase:
    def __init__(self, config: Config):
        self.config = config
        self.parent_pipe_pair = self.config.opts.pipe_pairs[0] if self.config.opts.pipe_pairs else None
        self.pipe_files = PipeFilesManager.new_one(self.config)

    def start(self):
        result = self.eval_model()
        p1_win, p1_draw, p1_lose = result
        p1_elo = self.compute_elo(p1_win, p1_draw)
        if self.parent_pipe_pair:
            self.parent_pipe_pair.open_write_nonblock()
            self.parent_pipe_pair.write(f'{p1_elo},{p1_win},{p1_draw},{p1_lose}'.encode())
            self.parent_pipe_pair.close_write()
        else:
            print(f'p1_elo:{p1_elo},win:{p1_win},draw:{p1_draw},lose:{p1_lose}'.encode())

    def build_versus_n_games_cmd(self, pipe_pairs):
        raise Exception('not implemented yet')

    def eval_model(self):

        pipe_pairs = self.pipe_files.make_pipes(1)
        cmd = self.build_versus_n_games_cmd(pipe_pairs=reverse_in_out(pipe_pairs))

        pipe_pairs[0].open_read_nonblock()
        start_child_proc(cmd=cmd).wait()

        result = pipe_pairs[0].read_no_empty()
        assert result
        result = result.decode()
        result = result.split(',')
        result = [int(x) for x in result]

        pipe_pairs[0].close_read()
        self.pipe_files.clear_pipes()

        return result

    def compute_elo(self, p1_win, p1_draw):
        expected = elo_lib.expected(self.config.opts.p1_elo, self.config.opts.p2_elo) * self.config.opts.n_games
        actual = p1_win + p1_draw / 2
        return elo_lib.elo(self.config.opts.p1_elo, expected, actual, self.config.opts.elo_k)


class EloWorker(EloWorkerBase):
    def __init__(self, config: Config):
        super().__init__(config)

    def build_versus_n_games_cmd(self, pipe_pairs):
        assert self.config.opts.p1_model_config_path
        assert self.config.opts.p1_model_weight_path
        assert self.config.opts.p2_model_config_path
        assert self.config.opts.p2_model_weight_path
        cmd = build_child_cmd(type='versus_n_games', config=self.config, pipe_pairs=pipe_pairs)
        cmd.extend([
            '--n-games', f'{self.config.opts.n_games}',
            '--n-workers', f'{self.config.opts.n_workers}',
            "--p1-model-config-path", self.config.opts.p1_model_config_path,
            "--p1-model-weight-path", self.config.opts.p1_model_weight_path,
            "--p2-model-config-path", self.config.opts.p2_model_config_path,
            "--p2-model-weight-path", self.config.opts.p2_model_weight_path,
        ])
        if self.config.opts.save_versus_dir:
            cmd.extend(["--save-versus-dir", self.config.opts.save_versus_dir])
        if self.config.opts.p1_first:
            cmd.extend(['--p1-first', f'{self.config.opts.p1_first}'])
        if self.config.opts.n_minutes:
            cmd.extend(['--n-minutes', f'{self.config.opts.n_minutes}'])
        return cmd
