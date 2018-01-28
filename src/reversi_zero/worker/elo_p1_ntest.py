import os
from logging import getLogger

from src.reversi_zero.config import Config
from src.reversi_zero.lib.model_helpler import ask_model_dir
from src.reversi_zero.lib.proc_helper import build_child_cmd
from src.reversi_zero.worker.elo_p1 import EloWorkerBase

logger = getLogger(__name__)


def start(config):
    if config.opts.ask_model:
        model_dir = ask_model_dir(config)
        config.resource.model_config_path = os.path.join(model_dir, config.resource.model_config_filename)
        config.resource.model_weight_path = os.path.join(model_dir, config.resource.model_weight_filename)
    return EloNTestWorker(config).start()


class EloNTestWorker(EloWorkerBase):
    def __init__(self, config: Config):
        super().__init__(config)

    def build_versus_n_games_cmd(self, pipe_pairs):
        cmd = build_child_cmd(type='versus_n_games_ntest', config=self.config, pipe_pairs=pipe_pairs)
        cmd.extend([
            '--n-games', f'{self.config.opts.n_games}',
            '--n-workers', f'{self.config.opts.n_workers}',
            "--model-config-path", self.config.resource.model_config_path,
            "--model-weight-path", self.config.resource.model_weight_path,
            '--ntest-depth', f'{self.config.opts.ntest_depth}',
            '--p1-name', f'ARZ:{self.config.play.simulation_num_per_move}',
            '--p2-name', f'NTest:{self.config.opts.ntest_depth}',
        ])
        if self.config.opts.save_versus_dir:
            cmd.extend(["--save-versus-dir", self.config.opts.save_versus_dir])
        if self.config.opts.p1_first:
            cmd.extend(['--p1-first', f'{self.config.opts.p1_first}'])
        return cmd
