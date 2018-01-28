from logging import getLogger

from src.reversi_zero.config import Config
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc
from src.reversi_zero.worker.versus_a_game_kernel import VersusPlayWorkerBase

logger = getLogger(__name__)


def start(config: Config):
    return VersusNTestWorker(config).start()


class VersusNTestWorker(VersusPlayWorkerBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start_p1_server(self, gtp_pipe_pair):
        cmd = build_child_cmd(type='gtp_server', config=self.config, pipe_pairs=[gtp_pipe_pair, self.p1_pipe_pair])
        return start_child_proc(cmd=cmd, nocuda=True)

    def start_p2_server(self, gtp_pipe_pair):
        cmd = build_child_cmd(type='gtp_server_ntest', config=self.config, pipe_pairs=[gtp_pipe_pair])
        cmd.extend([
            '--ntest-depth', f'{self.config.opts.ntest_depth}'
        ])
        return start_child_proc(cmd=cmd, nocuda=True)
