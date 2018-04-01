class PlayDataConfig:
    def __init__(self):
        self.nb_move_in_file = 300
        self.max_file_num = 500


class PlayConfig:
    def __init__(self):
        self.simulation_num_per_move = 100
        self.c_puct = 3
        self.noise_eps = 0.25
        self.dirichlet_alpha = 0.4
        self.change_tau_turn = 4
        self.virtual_loss = 3
        self.prediction_queue_size = 8
        self.can_resign = True
        self.v_resign_check_min_n = 100
        self.v_resign_init = -0.9
        self.v_resign_delta = 0.01
        self.v_resign_disable_prop = 0.1
        self.v_resign_false_positive_fraction_t_max = 0.05  # AZ: same
        self.v_resign_false_positive_fraction_t_min = 0.04  # AZ: UNKNOWN
        self.n_games_to_self_play = 999999999
        self.render = False
        self.model_check_interval_seconds = 10


class TrainerConfig:
    def __init__(self):
        self.batch_size = 4096
        self.start_total_steps = 0
        self.epoch_steps = 400
        self.save_model_steps = 1600
        self.generation_model_steps = 8000
        self.min_data_size_to_learn = 10
        self.lr_schedule = (  # (learning rate, before step count)
            (0.2,    50000),
            (0.02,   100000),
            (0.002,  200000),
            (0.0002, 9999999999)
        )
        self.need_eval = False


class ModelConfig:
    cnn_filter_num = 256
    cnn_filter_size = 3
    res_layer_num = 10
    l2_reg = 1e-4
    value_fc_size = 256
    input_size = (5,6,6)
    policy_size = 1+6*6
    model_step = None


class EnvSpecificConfig:
    def __init__(self):
        self.env_module_name = "src.reversi_zero.env.reversi6x6.reversi6x6_env"
        self.env_class_name = "Reversi6x6Env"


class EvalConfig:
    def __init__(self):
        self.n_games = 400
        self.win_lose_delta_threshold = 10
        self.p1_first = None
        self.p1_model_step = None
        self.p2_model_step = None



class ModelCacheConfig:
    def __init__(self):
        self.model_cache_size = None
