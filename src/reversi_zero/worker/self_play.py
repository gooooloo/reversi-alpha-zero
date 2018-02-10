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

    def start_model_cache_process(self, pipe_pairs):
        cmd = build_child_cmd(type='model_cache', config=self.config, pipe_pairs=pipe_pairs)
        cmd.extend([
            '--model-cache-size', f'{self.config.model_cache.model_cache_size}'
        ])
        return start_child_proc(cmd=cmd)

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

                pipe_pairs = self.pipe_files.make_pipes(2*self.config.opts.n_workers + 2)
                model_serving_pps = pipe_pairs[:self.config.opts.n_workers+1]
                model_cache_pps = pipe_pairs[self.config.opts.n_workers+1:] if self.config.model_cache.model_cache_size else None

                p = self.start_model_serving_process(model_serving_pps)
                ps.append(p)

                model_serving_pps[0].reverse_in_out().read_once(99)  # having response means 'ready', whatever it is.
                model_serving_pps = model_serving_pps[1:]

                if model_cache_pps:
                    p = self.start_model_cache_process(model_cache_pps)
                    ps.append(p)

                    model_cache_pps[0].reverse_in_out().read_once(99)  # having response means 'ready', whatever it is.
                    model_cache_pps = model_cache_pps[1:]

                if model_cache_pps:
                    for pp0, pp1 in zip(model_serving_pps, model_cache_pps):
                        pp0 = pp0.reverse_in_out()
                        pp1 = pp1.reverse_in_out()
                        p = self.start_a_self_play_process([pp0, pp1])
                        ps.append(p)
                else:
                    for pp0 in model_serving_pps:
                        pp0 = pp0.reverse_in_out()
                        p = self.start_a_self_play_process([pp0])
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

