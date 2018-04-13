import os

from src.reversi_zero.lib.nboard import GTPNBoardGameObj
from src.reversi_zero.worker.gtp_server import GTPServerWorker
from src.reversi_zero.worker.versus_a_game_kernel import VersusPlayWorkerBase
from src.reversi_zero.worker.versus_n_games import VersusWorkerBase

from src.reversi_zero.agent.api import MODEL_SERVING_READY, MODEL_SERVING_START, MODEL_SERVING_STARTED
from src.reversi_zero.config import Config
from src.reversi_zero.config import Options
from src.reversi_zero.lib.chunk_pb2 import ModelStep
from src.reversi_zero.lib.grpc_helper import GrpcClient, modelstep_to_simplestring, MODEL_STEP_TYPE_TO_EVAL, \
    MODEL_STEP_TYPE_NEWEST
from src.reversi_zero.lib.pipe_helper import PipeFilesManager
from src.reversi_zero.lib.pipe_helper import reverse_in_out
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc, build_child_cmd_with_module


def build_child_cmd_self(type, opts, pipe_pairs):
    return build_child_cmd_with_module(type=type,
                                       opts=opts,
                                       pipe_pairs=pipe_pairs,
                                       module='play.reversi_zero.ntest.run')


class EvalWorker:
    def __init__(self, config: Config):
        self.config = config
        assert not self.config.ipc.pipe_pairs
        self.pipe_files = PipeFilesManager.new_one(self.config)
        self.grpc_client = GrpcClient(self.config)

    def start(self):
        steps_to_eval = self.grpc_client.list_model_steps_to_eval()
        if not steps_to_eval:
            return

        step = 0 # TODO
        win_n,draw_n,lose_n = self.eval_model(step)

        print(f"{to_eval_model_dir}: {win_n} wins, {draw_n} draws, {lose_n} loses, ")

    def eval_model(self, step_to_eval):
        pipe_pairs = self.pipe_files.make_pipes(1)

        import copy
        opts = copy.copy(self.config.opts)
        opts.p1_model_step = modelstep_to_simplestring(ModelStep(type=MODEL_STEP_TYPE_TO_EVAL, step=step_to_eval))
        opts.p2_model_step = modelstep_to_simplestring(ModelStep(type=MODEL_STEP_TYPE_NEWEST, step=0))  # step doesn't matter here
        cmd = build_child_cmd_self(type='versus_n_games', opts=opts, pipe_pairs=reverse_in_out(pipe_pairs))
        pipe_pairs[0].open_read_nonblock()
        start_child_proc(cmd=cmd).wait()

        win = pipe_pairs[0].read_int(allow_empty=False)
        draw = pipe_pairs[0].read_int(allow_empty=False)
        lose = pipe_pairs[0].read_int(allow_empty=False)
        pipe_pairs[0].close_read()
        self.pipe_files.clear_pipes()

        return win,draw,lose


class EvalSomeWorker(VersusWorkerBase):

    def start_1_game_process(self, pps, p1_first):
        cmd = build_child_cmd_self(type='versus_one', config=self.config, pipe_pairs=pps)
        cmd.extend([
            '--ntest-depth', f'{self.config.opts.ntest_depth}',
            '--p1-name', self.config.opts.p1_name,
            '--p2-name', self.config.opts.p2_name,
            '--p1-first', f'{p1_first}',
        ])
        if self.config.opts.save_versus_dir:
            cmd.extend(["--save-versus-dir", self.config.opts.save_versus_dir])
        if self.config.opts.n_minutes:
            cmd.extend(['--n-minutes', f'{self.config.opts.n_minutes}'])
        return start_child_proc(cmd=cmd, nocuda=True)

    def start_model_serving_processes(self, p1_model_ready_pp, p2_model_ready_pp, p1_model_pps, p2_model_pps):
        p1_model_ready_pp.open_read_nonblock()
        self.start_model_serving_process(self.config.resource.model_config_path,
                                         self.config.resource.model_weight_path,
                                         reverse_in_out([p1_model_ready_pp] + p1_model_pps))

        x = p1_model_ready_pp.read_int(allow_empty=False)
        assert x == MODEL_SERVING_READY
        p1_model_ready_pp.open_write_nonblock()
        p1_model_ready_pp.write_int(MODEL_SERVING_START)
        p1_model_ready_pp.close_write()
        x = p1_model_ready_pp.read_int(allow_empty=False)
        assert x == MODEL_SERVING_STARTED

        p1_model_ready_pp.close_read()


class EvalOneWorker(VersusPlayWorkerBase):

    def start_p1_server(self, gtp_pipe_pair):
        cmd = build_child_cmd(type='gtp_server', config=self.config, pipe_pairs=[gtp_pipe_pair, self.p1_pipe_pair])
        if self.config.opts.n_minutes:
            cmd.extend(['--n-minutes', f'{self.config.opts.n_minutes}'])
        return start_child_proc(cmd=cmd, nocuda=True)

    def start_p2_server(self, gtp_pipe_pair):
        cmd = build_child_cmd_self(type='gtp_ntest', config=self.config, pipe_pairs=[gtp_pipe_pair])
        cmd.extend([
            '--ntest-depth', f'{self.config.opts.ntest_depth}'
        ])
        return start_child_proc(cmd=cmd, nocuda=True)


class NTestWorker(GTPServerWorker):

    def get_game_obj(self):

        class GTPNTestGameObj(GTPNBoardGameObj):
            def __init__(self, config):
                assert 'NTEST_HOME' in os.environ
                ntest_home = os.environ['NTEST_HOME']
                ntest_name = 'ntest'  # on OSX it should be mNTest, on Windows... I don't know
                depth = config.opts.ntest_depth
                super().__init__(cmd=ntest_name, cwd=ntest_home, depth=depth)

        return GTPNTestGameObj(self.config)


def main():

    opts = Options()
    opts.p2_model_step = modelstep_to_simplestring(ModelStep(type=MODEL_STEP_TYPE_NEWEST, step=0))  # step doesn't matter here
    config = Config(opts)

    if opts.cmd == 'eval':
        EvalWorker(config).start()
    elif opts.cmd == 'eval_n':
        EvalSomeWorker(config).start()
    elif opts.cmd == 'eval_one':
        EvalOneWorker(config).start()
    elif opts.cmd == 'gtp':
        NTestWorker(config).start()
    else:
        raise Exception(f'unsupported cmd {args.cmd}')


if __name__ == '__main__':
    main()