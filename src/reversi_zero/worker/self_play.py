from logging import getLogger
from time import sleep

from src.reversi_zero.agent.api import MODEL_SERVING_READY, MODEL_RELOAD_BEGIN, MODEL_RELOAD_END
from src.reversi_zero.agent.model_cache import MODEL_CACHE_READY, RESET_CACHE_START, RESET_CACHE_END
from src.reversi_zero.config import Config
from src.reversi_zero.lib.model_helpler import fetch_model_weight_digest
from src.reversi_zero.lib.pipe_helper import PipeFilesManager, reverse_in_out
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

        pipe_pairs = self.pipe_files.make_pipes(2*self.config.opts.n_workers + 2)
        model_serving_pps = pipe_pairs[:self.config.opts.n_workers+1]
        model_cache_pps = pipe_pairs[self.config.opts.n_workers+1:] if self.config.model_cache.model_cache_size else None

        self.start_model_serving_process(reverse_in_out(model_serving_pps))

        serving_and_me_pp = model_serving_pps[0]
        serving_and_me_pp.open_read_nonblock()  # won't close
        x = serving_and_me_pp.read_int(allow_empty=False)
        assert x == MODEL_SERVING_READY
        model_serving_pps = model_serving_pps[1:]

        if model_cache_pps:
            self.start_model_cache_process(reverse_in_out(model_cache_pps))

            cache_and_me_pp = model_cache_pps[0]
            cache_and_me_pp.open_read_nonblock()  # won't close
            x = cache_and_me_pp.read_int(allow_empty=False)
            assert x == MODEL_CACHE_READY
            model_cache_pps = model_cache_pps[1:]
        else:
            cache_and_me_pp = None

        if model_cache_pps:
            for pp0, pp1 in zip(model_serving_pps, model_cache_pps):
                self.start_a_self_play_process([pp0, pp1])
        else:
            for pp0 in model_serving_pps:
                self.start_a_self_play_process([pp0])

        digest = fetch_model_weight_digest(self.config)
        assert digest

        while True:
            now_digest = fetch_model_weight_digest(self.config)
            logger.info(f'old digets: {digest}')
            logger.info(f'now digets: {now_digest}')
            if now_digest == digest:
                sleep(600)
                continue
            else:
                logger.info('reset cache start')

                if cache_and_me_pp:
                    cache_and_me_pp.open_write_nonblock()
                    cache_and_me_pp.write_int(RESET_CACHE_START)
                    cache_and_me_pp.close_write()

                serving_and_me_pp.open_write_nonblock()
                serving_and_me_pp.write_int(MODEL_RELOAD_BEGIN)
                serving_and_me_pp.close_write()

                x = serving_and_me_pp.read_int(allow_empty=False)
                assert x == MODEL_RELOAD_END

                if cache_and_me_pp:
                    cache_and_me_pp.open_write_nonblock()
                    cache_and_me_pp.write_int(RESET_CACHE_END)
                    cache_and_me_pp.close_write()

                logger.info('reset cache finish')

                digest = fetch_model_weight_digest(self.config)
                assert digest

