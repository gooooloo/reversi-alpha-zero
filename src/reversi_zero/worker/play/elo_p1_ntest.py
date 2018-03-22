import os
import re
from logging import getLogger

from src.reversi_zero.config import Config
from src.reversi_zero.lib.model_helpler import ask_model_dir
from src.reversi_zero.lib.proc_helper import build_child_cmd
from src.reversi_zero.worker.play.elo_p1 import EloWorkerBase

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

        self.model_generation = self.extract_model_generation(config.resource.model_weight_path)

    def build_versus_n_games_cmd(self, pipe_pairs):
        import copy
        opts = copy.copy(self.config.opts)
        opts.model_config_path = self.config.resource.model_config_path
        opts.model_weight_path = self.config.resource.model_weight_path
        opts.p1_name = self.get_p1_name()
        opts.p2_name = self.get_p2_name()

        cmd = build_child_cmd(type='versus_n_games_ntest', opts=opts, pipe_pairs=pipe_pairs)
        return cmd

    def get_p1_name(self):
        if self.model_generation is not None:
            if self.config.opts.n_minutes:
                return f'ARZ:{self.model_generation}:{self.config.opts.n_minutes}min'
            else:
                return f'ARZ:{self.model_generation}:{self.config.play.simulation_num_per_move}'
        else:
            return f'ARZ:{self.config.play.simulation_num_per_move}'

    def get_p2_name(self):
            return f'NTest:{self.config.opts.ntest_depth}'

    def extract_model_generation(self, model_weight_path):
        assert '%s' in self.config.resource.generation_model_dirname_tmpl
        p = self.config.resource.generation_model_dirname_tmpl.replace('%s', '(\d+)')
        p = f'.*{p}.*'
        p = re.compile(p)
        m = p.match(model_weight_path)
        gen = m.group(1) if m else None
        return gen
