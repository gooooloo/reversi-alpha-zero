class PlayDataConfig:
    def __init__(self):
        self.nb_game_in_file = 100
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
        self.parallel_search_num = 8
        self.prediction_worker_sleep_sec  = 0.0001
        self.wait_for_expanding_sleep_sec = 0.00001
        self.can_resign = True
        self.v_resign_check_min_n = 100
        self.v_resign_init = -0.9
        self.v_resign_delta = 0.01
        self.v_resign_disable_prop = 0.1
        self.v_resign_false_positive_fraction_t_max = 0.05  # AZ: same
        self.v_resign_false_positive_fraction_t_min = 0.04  # AZ: UNKNOWN
        self.n_games_to_self_play = 999999999
        self.render = False
        self.model_check_interval_seconds = 60  # if too small, model reloading will waste to much self play time.


class TrainerConfig:
    def __init__(self):
        self.batch_size = 4096
        self.epoch_to_checkpoint = 1
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


class PlayWithHumanConfig:
    def __init__(self):
        self.noise_eps = 0
        self.change_tau_turn = 0

    def update_play_config(self, pc):
        pc.noise_eps = self.noise_eps
        pc.change_tau_turn = self.change_tau_turn


class EnvSpecificConfig:
    def __init__(self):
        self.env_arg_name = "reversi6x6"
        self.env_module_name = "reversi_zero.env.reversi_generic_env"
        self.env_class_name = "Reversi6x6Env"
        self.board_edge_size = 6


class GuiConfig:
    def __init__(self):
        self.window_size = (400, 440)
        self.window_title = "reverse-6x6-alpha-zero"
        self.EDGE_LENGTH = 6
        self.x_is_vertical = True


class EvalConfig:
    def __init__(self):
        self.elo_k = 32
        self.n_games = 400
        self.elo_threshold = 300


class TimeConfig:
    def __init__(self):
        self.whole_move_num = 32
        self.endgame_move_num = 10
        self.decay_factor = 0.9


class ModelCacheConfig:
    def __init__(self):
        self.model_cache_size = None
