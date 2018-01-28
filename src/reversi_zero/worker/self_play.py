from logging import getLogger
from time import sleep

from src.reversi_zero.config import Config
from src.reversi_zero.lib.model_helpler import fetch_model_weight_digest
from src.reversi_zero.lib.pipe_helper import PipeFilesManager
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

logger = getLogger(__name__)


def start(config: Config):
    return SelfWorker(config).start()


class SelfWorker:
    def __init__(self, config):
        self.config = config
        assert not self.config.opts.pipe_pairs
        self.pipe_files = PipeFilesManager.new_one(self.config)

    def start_model_serving_process(self, pipe_pairs):
        cmd = build_child_cmd(type='model_serving', config=self.config, pipe_pairs=pipe_pairs)
        cmd.extend([
            '--model-config-path', self.config.resource.model_config_path,
            '--model-weight-path', self.config.resource.model_weight_path,
        ])
        return start_child_proc(cmd=cmd)

    def start_a_self_play_process(self, pipe_pairs):
        cmd = build_child_cmd(type='self_play_kernel', config=self.config, pipe_pairs=pipe_pairs)
        cmd.extend([
            '--can-resign', f'{self.config.play.can_resign}',
            '--n-games', f'{9999999999}',
        ])
        return start_child_proc(cmd=cmd, nocuda=True)

    def start(self):

        digest = None
        ps = None
        while True:
            if digest is None:
                ps = []

                pipe_pairs = self.pipe_files.make_pipes(self.config.opts.n_workers + 1)
                p = self.start_model_serving_process(pipe_pairs)
                ps.append(p)

                pipe_pairs[0].reverse_in_out().read_once(99)  # having response means 'ready', whatever it is.
                pipe_pairs = pipe_pairs[1:]

                for pp in pipe_pairs:
                    pp = pp.reverse_in_out()
                    p = self.start_a_self_play_process([pp])
                    ps.append(p)

                digest = fetch_model_weight_digest(self.config)
                assert digest

            else:
                now_digest = fetch_model_weight_digest(self.config)
                print(f'old digets: {digest}')
                print(f'now digets: {now_digest}')
                if now_digest == digest:
                    sleep(600)
                    continue
                else:
                    for p in reversed(ps):
                        p.kill()
                    ps = None
                    self.pipe_files.clear_pipes()
                    digest = None

