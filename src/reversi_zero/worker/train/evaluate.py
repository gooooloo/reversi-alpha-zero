import os
import shutil
from logging import getLogger
from time import sleep
from natsort import natsorted, ns

from src.reversi_zero.config import Config
from src.reversi_zero.lib.pipe_helper import PipeFilesManager, reverse_in_out
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

logger = getLogger(__name__)


def start(config: Config):
    return EvaluateWorker(config).start()


class EvaluateWorker:
    def __init__(self, config: Config):
        self.config = config
        assert not self.config.opts.pipe_pairs
        self.pipe_files = PipeFilesManager.new_one(self.config)

    def start(self):
        rc = self.config.resource
        while True:
            to_eval_model_dir = self.get_to_eval_model_dir()
            if to_eval_model_dir is None:
                logger.info('no model to eval. sleeping.')
                sleep(60)
                continue

            to_eval_config_path = os.path.join(to_eval_model_dir, rc.model_config_filename)
            to_eval_weight_path = os.path.join(to_eval_model_dir, rc.model_weight_filename)

            elo,win_n,draw_n,lose_n = self.eval_model_elo(to_eval_config_path, to_eval_weight_path)

            with open(self.config.resource.eval_result_path, "at") as f:
                f.write(f"{to_eval_model_dir}: {win_n} wins, {draw_n} draws, {lose_n} loses, "
                        f"{elo} elo, {'>=' if elo >= self.config.eval.elo_threshold else '<'} "
                        f"threshold({self.config.eval.elo_threshold}). \n")

            if elo >= self.config.eval.elo_threshold:
                logger.info(f"Congrats! Better model! ELO vs current_model= {elo}")
                logger.info(f"Will update model with {to_eval_model_dir}")
                shutil.copyfile(to_eval_config_path, rc.model_config_path)
                shutil.copyfile(to_eval_weight_path, rc.model_weight_path)
                shutil.move(to_eval_model_dir, rc.generation_model_dir)
            else:
                logger.info(f"Sorry! Model not good enough! ELO vs current_model= {elo}")
                shutil.rmtree(to_eval_model_dir, ignore_errors=True)

    def get_to_eval_model_dir(self):
        rc = self.config.resource
        d = rc.to_eval_model_dir
        dirs = [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]
        for sd in reversed(natsorted(dirs, alg=ns.IGNORECASE)):
            return sd

        return None

    def eval_model_elo(self, to_eval_config_path, to_eval_weight_path):
        rc = self.config.resource

        pipe_pairs = self.pipe_files.make_pipes(1)

        import copy
        opts = copy.copy(self.config.opts)
        opts.p1_model_config_path = to_eval_config_path
        opts.p1_model_weight_path = to_eval_weight_path
        opts.p2_model_config_path = rc.model_config_path
        opts.p2_model_weight_path = rc.model_weight_path
        opts.p1_elo = 0
        opts.p2_elo = 0

        cmd = build_child_cmd(type='elo_p1', opts=opts, pipe_pairs=reverse_in_out(pipe_pairs))
        pipe_pairs[0].open_read_nonblock()
        start_child_proc(cmd=cmd).wait()

        result = pipe_pairs[0].read_no_empty()
        result = result.decode()
        result = result.split(',')
        elo = float(result[0])
        win = int(result[1])
        draw = int(result[2])
        lose = int(result[3])
        self.pipe_files.clear_pipes()

        return elo,win,draw,lose
