from logging import getLogger
from time import sleep

from src.reversi_zero.agent.api import MODEL_SERVING_READY, MODEL_SERVING_START, MODEL_SERVING_STOP, \
    MODEL_SERVING_STARTED, MODEL_SERVING_STOPPED
from src.reversi_zero.agent.model_cache import MODEL_CACHE_READY, RESET_CACHE_START, RESET_CACHE_END
from src.reversi_zero.config import Config
from src.reversi_zero.lib.model_helpler import fetch_model_step_info
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
        if self.config.opts.gpu_mem_frac is not None:
            self.config.opts.gpu_mem_frac /= 2

    def start_model_cache_process(self, pipe_pairs):
        cmd = build_child_cmd(type='model_cache', opts=self.config.opts, pipe_pairs=pipe_pairs)
        return start_child_proc(cmd=cmd)

    def start_model_serving_process(self, pipe_pairs, model_serving_step_check=None):
        import copy
        opts = copy.copy(self.config.opts)
        opts.model_config_path = self.config.resource.model_config_path
        opts.model_weight_path = self.config.resource.model_weight_path
        opts.model_serving_step_check = model_serving_step_check
        cmd = build_child_cmd(type='model_serving', opts=opts, pipe_pairs=pipe_pairs)
        return start_child_proc(cmd=cmd)

    def start_a_self_play_process(self, pipe_pairs):
        cmd = build_child_cmd(type='self_play_kernel', opts=self.config.opts, pipe_pairs=pipe_pairs)
        return start_child_proc(cmd=cmd, nocuda=True)

    def fetch_model_step_info(self):
        step_info = None
        while step_info is None:
            step_info = fetch_model_step_info(self.config)
        return step_info

    def start(self):

        pipe_pairs = self.pipe_files.make_pipes(2*self.config.opts.n_workers + 2)
        model_serving_pps = pipe_pairs[:self.config.opts.n_workers+1]
        model_cache_pps = pipe_pairs[self.config.opts.n_workers+1:] if self.config.model_cache.model_cache_size else None

        model_serving_process = self.start_model_serving_process(reverse_in_out(model_serving_pps))

        serving_and_me_pp = model_serving_pps[0]
        serving_and_me_pp.open_read_nonblock()  # will close very late.
        x = serving_and_me_pp.read_int(allow_empty=False)
        assert x == MODEL_SERVING_READY

        serving_and_me_pp.open_write_nonblock()
        serving_and_me_pp.write_int(MODEL_SERVING_START)
        serving_and_me_pp.close_write()
        x = serving_and_me_pp.read_int(allow_empty=False)
        assert x == MODEL_SERVING_STARTED

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

        model_step = self.fetch_model_step_info()
        assert model_step is not None

        while True:
            now_model_step = self.fetch_model_step_info()
            logger.info(f'old model step: {model_step}')
            logger.info(f'now model step: {now_model_step}')
            if now_model_step <= model_step:
                if now_model_step < model_step:
                    # have no idea why it happens, but it does...
                    logger.info(f'now model step smaller than old model. WIRED!!')
                sleep(self.config.play.model_check_interval_seconds)
                continue
                sleep(self.config.play.model_check_interval_seconds)
                continue
            else:
                model_step = now_model_step

                if cache_and_me_pp:
                    logger.info('reset cache start')
                    cache_and_me_pp.open_write_nonblock()
                    cache_and_me_pp.write_int(RESET_CACHE_START)
                    cache_and_me_pp.close_write()

                tmp_serving_and_me_pp = self.pipe_files.make_pipes(1)[0]
                tmp_model_serving_pps = [tmp_serving_and_me_pp] + model_serving_pps
                tmp_serving_and_me_pp.open_read_nonblock()  # will close very late.
                tmp_model_serving_process = self.start_model_serving_process(reverse_in_out(tmp_model_serving_pps), model_step)

                x = tmp_serving_and_me_pp.read_int(allow_empty=False)
                assert x == MODEL_SERVING_READY

                serving_and_me_pp.open_write_nonblock()
                serving_and_me_pp.write_int(MODEL_SERVING_STOP)
                serving_and_me_pp.close_write()
                x = serving_and_me_pp.read_int(allow_empty=False)
                assert x == MODEL_SERVING_STOPPED

                tmp_serving_and_me_pp.open_write_nonblock()
                tmp_serving_and_me_pp.write_int(MODEL_SERVING_START)
                tmp_serving_and_me_pp.close_write()
                x = tmp_serving_and_me_pp.read_int(allow_empty=False)
                assert x == MODEL_SERVING_STARTED

                model_serving_process.kill()
                serving_and_me_pp.close_read()
                self.pipe_files.clear_a_pipe(serving_and_me_pp)

                model_serving_process = tmp_model_serving_process
                serving_and_me_pp = tmp_serving_and_me_pp

                if cache_and_me_pp:
                    cache_and_me_pp.open_write_nonblock()
                    cache_and_me_pp.write_int(RESET_CACHE_END)
                    cache_and_me_pp.close_write()
                    logger.info('reset cache finish')

