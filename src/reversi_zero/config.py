import os


def _project_dir():
    d = os.path.dirname
    return d(d(d(os.path.abspath(__file__))))


def _data_dir(env):
    return os.path.join(os.path.join(_project_dir(), "data"), env)


class Config:
    def __init__(self, opts):
        if opts.env == 'reversi':
            from src.reversi_zero.env.reversi import reversi_config as env_specific
        elif opts.env == 'reversi4x4':
            from src.reversi_zero.env.reversi4x4 import reversi4x4_config as env_specific
        elif opts.env == 'reversi6x6':
            from src.reversi_zero.env.reversi6x6 import reversi6x6_config as env_specific
        else:
            raise Exception(f"unknown env: {opts.env}")

        self.opts = opts

        self.env = env_specific.EnvSpecificConfig()
        self.eval = env_specific.EvalConfig()
        self.model = env_specific.ModelConfig()
        self.model_cache = env_specific.ModelCacheConfig()
        self.play = env_specific.PlayConfig()
        self.play_data = env_specific.PlayDataConfig()
        self.resource = ResourceConfig(opts.env, opts.dir)
        self.trainer = env_specific.TrainerConfig()
        self.gpu = GPUConfig()
        self.ipc = IPCConfig()

        self.setup()

    def setup(self):

        if self.opts.start_total_steps is not None:
            self.trainer.start_total_steps = self.opts.start_total_steps

        self.resource.create_directories()

        self.trainer.need_eval = self.opts.need_eval

        if self.opts.can_resign is not None:
            self.play.can_resign = self.opts.can_resign
        if self.opts.n_sims is not None:
            self.play.simulation_num_per_move = self.opts.n_sims

        if self.opts.model_cache_size is not None:
            self.model_cache.model_cache_size = self.opts.model_cache_size

        if self.opts.gpu_mem_frac is not None:
            self.gpu.gpu_mem_frac = self.opts.gpu_mem_frac

        if self.opts.fs_ip is not None:
            self.ipc.fs_ip = self.opts.fs_ip
        if self.opts.fs_port is not None:
            self.ipc.fs_port = self.opts.fs_port
        if self.opts.pipe_pairs is not None:
            from src.reversi_zero.lib.pipe_helper import load_pipe_pairs_names
            self.ipc.pipe_pairs = load_pipe_pairs_names(self.opts.pipe_pairs)
        if self.opts.n_workers is not None:
            self.ipc.n_workers = self.opts.n_workers

        if self.opts.n_games is not None:
            self.eval.n_games = self.opts.n_games
        if self.opts.p1_first is not None:
            self.eval.p1_first = self.opts.p1_first
        if self.opts.p1_model_step is not None:
            self.eval.p1_model_step = self.opts.p1_model_step
        if self.opts.p2_model_step is not None:
            self.eval.p2_model_step = self.opts.p2_model_step

        if self.opts.model_step is not None:
            self.model.model_step = self.opts.model_step


# This class is just for config overwriting. Should not use it in logic codes directly.
class Options:
    def __init__(self):
        self.can_resign = None
        self.cmd = None
        self.dir = None
        self.env = None
        self.fs_ip = None
        self.fs_port = None
        self.gpu_mem_frac = None
        self.model_cache_size = None
        self.model_step = None
        self.n_games = None
        self.n_sims = None
        self.n_workers = None
        self.need_eval = None
        self.p1_first = None
        self.p1_model_step = None
        self.p2_model_step = None
        self.pipe_pairs = None
        self.start_total_steps = None


class IPCConfig:
    def __init__(self):
        self.fs_ip = None
        self.fs_port = None
        self.pipe_pairs = None
        self.n_workers = None


class GPUConfig:
    def __init__(self):
        self.gpu_mem_frac = None


class ResourceConfig:
    def __init__(self, env, dir):
        self.project_dir = dir or _project_dir()
        self.data_dir = _data_dir(env)
        self.model_dir = os.path.join(self.data_dir, "model")
        self.model_config_filename = "model_config.json"
        self.model_weight_filename = "model_weight.h5"
        self.model_config_path = os.path.join(self.model_dir, self.model_config_filename)
        self.model_weight_path = os.path.join(self.model_dir, self.model_weight_filename)

        self.archive_model_dir = os.path.join(self.model_dir, "archive_models")
        self.archive_model_dirname_tmpl = "model_%s_steps"

        self.to_eval_model_dir = os.path.join(self.model_dir, "to_eval")
        self.to_eval_model_dirname_tmpl = "model_%s_steps"
        self.eval_result_path = os.path.join(self.to_eval_model_dir, "eval.result.txt")

        self.eval_ggf_dir = os.path.join(self.data_dir, "eval_ggf")

        self.play_data_dir = os.path.join(self.data_dir, "play_data")
        self.play_data_filename_tmpl = "play_%s.json"
        self.play_data_statistics_filename = "play_data_statistics.log"

        self.log_dir = os.path.join(self.project_dir, "logs")
        self.main_log_path = os.path.join(self.log_dir, "main.log")
        self.resign_log_dir = self.log_dir
        self.resign_log_path = os.path.join(self.resign_log_dir, "resign.log")

    def create_directories(self):
        dirs = [self.project_dir, self.data_dir, self.model_dir, self.play_data_dir, self.log_dir,
                self.archive_model_dir, self.to_eval_model_dir]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
