from logging import getLogger

from src.reversi_zero.config import Config
from src.reversi_zero.lib.pipe_helper import reverse_in_out
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc
from src.reversi_zero.worker.versus_n_games import VersusWorkerBase

logger = getLogger(__name__)


def start(config: Config):
    return VersusNTestWorker(config).start()


class VersusNTestWorker(VersusWorkerBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start_1_game_process(self, pps, p1_first):
        cmd = build_child_cmd(type='versus_a_game_kernel_ntest', config=self.config, pipe_pairs=pps)
        cmd.extend([
            '--ntest-depth', f'{self.config.opts.ntest_depth}',
            '--p1-name', self.config.opts.p1_name,
            '--p2-name', self.config.opts.p2_name,
        ])
        if self.config.opts.p1_first:
            cmd.extend(['--p1-first', self.config.opts.p1_first])
        if self.config.opts.save_versus_dir:
            cmd.extend(["--save-versus-dir", self.config.opts.save_versus_dir])
        return start_child_proc(cmd=cmd, nocuda=True)

    def start_model_serving_processes(self, p1_model_ready_pp, p2_model_ready_pp, p1_model_pps, p2_model_pps):
        p1_model_ready_pp.open_read_nonblock()
        self.start_model_serving_process(self.config.resource.model_config_path,
                                         self.config.resource.model_weight_path,
                                         reverse_in_out([p1_model_ready_pp] + p1_model_pps))

        p1_model_ready_pp.read_no_empty(99, sleep_retry=0.1)  # having response means 'ready', whatever it is.
        p1_model_ready_pp.close_read()
