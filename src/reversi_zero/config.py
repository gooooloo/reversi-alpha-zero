import os

def _project_dir():
    d = os.path.dirname
    return d(d(d(os.path.abspath(__file__))))


def _data_dir(env):
    return os.path.join(os.path.join(_project_dir(), "data"), env)


class Config:
    def __init__(self, env):
        if env == 'reversi':
            from .configs import reversi_config as env_specific
        elif env == 'reversi4x4':
            from .configs import reversi4x4_config as env_specific
        elif env == 'reversi6x6':
            from .configs import reversi6x6_config as env_specific
        else:
            raise Exception(f"unknown env: {env}")

        self.opts = Options()
        self.resource = ResourceConfig(env)
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
    pipe_pairs = None
    n_workers = 1
    n_games = 9999999999
    gpu_mem_frac = None
    p1_model_config_path = None
    p1_model_weight_path = None
    p2_model_config_path = None
    p2_model_weight_path = None
    p1_elo = None
    p2_elo = None
    elo_k = None
    http_port = None
    http_url = None
    ask_model = None
    p1_n_sims = None
    p2_n_sims = None
    league_result = None
    p1_first = None
    ntest_depth = 1
    save_versus_dir = None
    p1_name = None
    p2_name = None
    n_minutes = None


class ResourceConfig:
    def __init__(self, env):
        self.project_dir = os.environ.get("PROJECT_DIR", _project_dir())
        self.data_dir = os.environ.get("DATA_DIR", _data_dir(env))
        self.model_dir = os.environ.get("MODEL_DIR", os.path.join(self.data_dir, "model"))
        self.model_config_filename = "model_config.json"
        self.model_weight_filename = "model_weight.h5"
        self.model_config_path = os.path.join(self.model_dir, self.model_config_filename)
        self.model_weight_path = os.path.join(self.model_dir, self.model_weight_filename)

        self.use_remote_model = os.environ.get("USE_REMOTE_MODEL")
        self.remote_model_config_path = os.environ.get("MODEL_CONFIG_URL")
        self.remote_model_weight_path = os.environ.get("MODEL_WEIGHT_URL")
        if self.use_remote_model and not self.remote_model_config_path:
            raise Exception("USE_REMOTE_MODEL is True but MODEL_CONFIG_URL is not set!")
        if self.use_remote_model and not self.remote_model_weight_path:
            raise Exception("USE_REMOTE_MODEL is True but MODEL_WEIGHT_URL is not set!")

        self.generation_model_dir = os.path.join(self.model_dir, "generation_models")
        self.generation_model_dirname_tmpl = "model_%s-steps"

        self.to_eval_model_dir = os.path.join(self.model_dir, "to_eval")
        self.to_eval_model_dirname_tmpl = "model_%s-steps"
        self.eval_result_path = os.path.join(self.to_eval_model_dir, "eval.result.txt")

        self.play_data_dir = os.path.join(self.data_dir, "play_data")
        self.play_data_filename_tmpl = "play_%s.json"

        self.log_dir = os.path.join(self.project_dir, "logs")
        self.main_log_path = os.path.join(self.log_dir, "main.log")
        self.resign_log_dir = self.log_dir
        self.resign_log_path = os.path.join(self.resign_log_dir, "resign.log")
        self.resign_delta_path_tmpl = "resign_delta_%s.log"
        self.remote_resign_log_path = os.environ.get("RESIGN_CTRL_URL")

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

