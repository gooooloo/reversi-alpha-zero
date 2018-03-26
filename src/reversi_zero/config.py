import os

def _project_dir():
    d = os.path.dirname
    return d(d(d(os.path.abspath(__file__))))


def _data_dir(env):
    return os.path.join(os.path.join(_project_dir(), "data"), env)


class Config:
    def __init__(self, opts):
        if opts.env == 'reversi':
            from .configs import reversi_config as env_specific
        elif opts.env == 'reversi4x4':
            from .configs import reversi4x4_config as env_specific
        elif opts.env == 'reversi6x6':
            from .configs import reversi6x6_config as env_specific
        else:
            raise Exception(f"unknown env: {opts.env}")

        self.opts = opts
        self.resource = ResourceConfig(opts.env)
        self.gui = env_specific.GuiConfig()

        self.model = env_specific.ModelConfig()
        self.play = env_specific.PlayConfig()
        self.play_data = env_specific.PlayDataConfig()
        self.trainer = env_specific.TrainerConfig()

        self.env = env_specific.EnvSpecificConfig()

        self.play_with_human_config = env_specific.PlayWithHumanConfig()

        self.eval = env_specific.EvalConfig()

        self.time = env_specific.TimeConfig()

        self.model_cache = env_specific.ModelCacheConfig()


class Options:
    def __init__(self):
        self.ask_model = None
        self.can_resign = None
        self.cmd = None
        self.elo_k = None
        self.env = None
        self.gpu_mem_frac = None
        self.http_port = None
        self.http_url = None
        self.league_result = None
        self.model_cache_size = None
        self.model_config_path = None
        self.model_serving_step_check = None
        self.model_weight_path = None
        self.n_games = 9999999999
        self.n_minutes = None
        self.n_sims = None
        self.n_steps_model = None
        self.n_workers = 1
        self.need_eval = None
        self.ntest_depth = 1
        self.p1_elo = None
        self.p1_first = None
        self.p1_model_config_path = None
        self.p1_model_weight_path = None
        self.p1_n_sims = None
        self.p1_name = None
        self.p2_elo = None
        self.p2_model_config_path = None
        self.p2_model_weight_path = None
        self.p2_n_sims = None
        self.p2_name = None
        self.pipe_pairs = None
        self.pipes = None
        self.render = None
        self.save_versus_dir = None
        self.start_total_steps = None
        self.total_step = None


class ResourceConfig:
    def __init__(self, env):
        self.project_dir = _project_dir()
        self.data_dir = _data_dir(env)
        self.model_dir = os.path.join(self.data_dir, "model")
        self.model_config_filename = "model_config.json"
        self.model_weight_filename = "model_weight.h5"
        self.model_config_path = os.path.join(self.model_dir, self.model_config_filename)
        self.model_weight_path = os.path.join(self.model_dir, self.model_weight_filename)

        self.remote_http_server = None
        self.remote_play_data_path = "play_data"
        self.remote_model_config_path = "model_config"
        self.remote_model_weight_path = "model_weight"
        self.remote_resign_path = "resign"

        self.generation_model_dir = os.path.join(self.model_dir, "generation_models")
        self.generation_model_dirname_tmpl = "model_%s-steps"

        self.to_eval_model_dir = os.path.join(self.model_dir, "to_eval")
        self.to_eval_model_dirname_tmpl = "model_%s-steps"
        self.eval_result_path = os.path.join(self.to_eval_model_dir, "eval.result.txt")

        self.play_data_dir = os.path.join(self.data_dir, "play_data")
        self.play_data_filename_tmpl = "play_%s.json"
        self.play_data_statistics_filename = "play_data_statistics.log"

        self.log_dir = os.path.join(self.project_dir, "logs")
        self.main_log_path = os.path.join(self.log_dir, "main.log")
        self.resign_log_dir = self.log_dir
        self.resign_log_path = os.path.join(self.resign_log_dir, "resign.log")

    def create_directories(self):
        dirs = [self.project_dir, self.data_dir, self.model_dir, self.play_data_dir, self.log_dir,
                self.generation_model_dir]
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)


class GuiConfig:
    def __init__(self, env):
        self.window_size = (400, 440)
        self.window_title = f"{env}-alpha-zero"



class EloConfig:
    def __init__(self):
        self.noise_eps = 0
        self.change_tau_turn = 0

    def update_play_config(self, pc):
        pc.noise_eps = self.noise_eps
        pc.change_tau_turn = self.change_tau_turn

