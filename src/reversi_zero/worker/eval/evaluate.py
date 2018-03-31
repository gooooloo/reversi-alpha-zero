from logging import getLogger
from time import sleep

from src.reversi_zero.config import Config
from src.reversi_zero.lib.chunk_pb2 import ModelStep
from src.reversi_zero.lib.grpc_helper import GrpcClient, modelstep_to_simplestring, MODEL_STEP_TYPE_TO_EVAL, \
    MODEL_STEP_TYPE_NEWEST
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
        self.grpc_client = GrpcClient(self.config)

    def start(self):
        while True:
            steps_to_eval = self.grpc_client.list_model_steps_to_eval()
            if not steps_to_eval:
                sleep(60)
                continue

            step = sorted(steps_to_eval)[-1]

            win_n,draw_n,lose_n = self.eval_model(step)

            delta = win_n - lose_n
            with open(self.config.resource.eval_result_path, "at") as f:
                f.write(f"{to_eval_model_dir}: {win_n} wins, {draw_n} draws, {lose_n} loses, "
                        f"{delta} delta, {'>=' if delta >= self.config.eval.win_lose_delta_threshold else '<'} "
                        f"threshold({self.config.eval.win_lose_delta_threshold}). \n")

            model_step = ModelStep(type=MODEL_STEP_TYPE_TO_EVAL, step=step)
            if delta >= self.config.eval.win_lose_delta_threshold:
                logger.info(f"Congrats! Better model! #win - #lose (vs current_model) = {delta}")
                logger.info(f"Will update model with step {step}")
                self.grpc_client.report_better_model(model_step)
            else:
                logger.info(f"Sorry! Model not good enough! #win - #lose (vs current_model) = {delta}")
                self.grpc_client.remove_model(model_step)

    def eval_model(self, step_to_eval):
        pipe_pairs = self.pipe_files.make_pipes(1)

        import copy
        opts = copy.copy(self.config.opts)
        opts.p1_model_step = modelstep_to_simplestring(ModelStep(type=MODEL_STEP_TYPE_TO_EVAL, step=step_to_eval))
        opts.p2_model_step = modelstep_to_simplestring(ModelStep(type=MODEL_STEP_TYPE_NEWEST, step=0))  # step doesn't matter here

        cmd = build_child_cmd(type='versus_n_games', opts=opts, pipe_pairs=reverse_in_out(pipe_pairs))
        pipe_pairs[0].open_read_nonblock()
        start_child_proc(cmd=cmd).wait()

        win = pipe_pairs[0].read_int(allow_empty=False)
        draw = pipe_pairs[0].read_int(allow_empty=False)
        lose = pipe_pairs[0].read_int(allow_empty=False)
        pipe_pairs[0].close_read()
        self.pipe_files.clear_pipes()

        return win,draw,lose
