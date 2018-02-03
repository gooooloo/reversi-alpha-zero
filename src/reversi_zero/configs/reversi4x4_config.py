class PlayDataConfig:
    def __init__(self):
        self.nb_game_in_file = 1000
        self.max_file_num = 500


class PlayConfig:
    def __init__(self):
        self.simulation_num_per_move = 100  # AZ:800, AGZ:1600
        self.c_puct = 3                     # AZ: UNKNOWN
        self.noise_eps = 0.25               # AZ: same
        self.dirichlet_alpha = 0.4          # AZ: depends on game
        self.change_tau_turn = 4            # AZ: 30
        self.virtual_loss = 3               # AZ: UNKNOWN
        self.prediction_queue_size = 8      # AZ: 8
        self.parallel_search_num = 8        # AZ: N/A
        self.prediction_worker_sleep_sec  = 0.0001
        self.wait_for_expanding_sleep_sec = 0.00001
        self.can_resign = True
        self.v_resign_check_min_n = 100
        self.v_resign_init = -0.65          # AZ: UNKNOWN
        self.v_resign_delta = 0.01          # AZ: UNKNOWN
        self.v_resign_disable_prop = 0.1    # AZ: same
        self.v_resign_false_positive_fraction_t_max = 0.05  # AZ: same
        # If we don't have a min fraction, then we may have a lower frac, in worst case we will have NO
        # resignation. Than means we will have to train many 1-side games. Not what we want.
        self.v_resign_false_positive_fraction_t_min = 0.04  # AZ: UNKNOWN
        self.n_games_to_self_play = 999999999
        self.render = False


class TrainerConfig:
    def __init__(self):
        self.batch_size = 4096
        self.epoch_to_checkpoint = 1
        self.start_total_steps = 0
        self.epoch_steps = 100
        self.save_model_steps = 100
        self.generation_model_steps = 300
        self.min_data_size_to_learn = 10000
        self.lr_schedule = (  # (learning rate, before step count)
            (0.2,    10000),
            (0.02,   20000),
            (0.002,  30000),
            (0.0002, 9999999999)
        )
        self.need_eval = False


class ModelConfig:
    cnn_filter_num = 256
    cnn_filter_size = 3
    res_layer_num = 10
    l2_reg = 1e-4
    value_fc_size = 256
    input_size = (3,4,4)
    policy_size = 1+4*4


class PlayWithHumanConfig:
    def __init__(self):
        self.noise_eps = 0
        self.change_tau_turn = 0

    def update_play_config(self, pc):
        pc.noise_eps = self.noise_eps
        pc.change_tau_turn = self.change_tau_turn


class EnvSpecificConfig:
    def __init__(self):
        self.env_arg_name = "reversi4x4"
        self.env_module_name = "reversi_zero.env.reversi_generic_env"
        self.env_class_name = "Reversi4x4Env"
        self.board_edge_size = 4

class GuiConfig:
    def __init__(self):
        self.window_size = (400, 440)
        self.window_title = "reversi-4x4-alpha-zero"
        self.EDGE_LENGTH = 4
        self.x_is_vertical = True


class EvalConfig:
    def __init__(self):
        self.elo_k = 32
        self.n_games = 400
        self.elo_threshold = 150  # #win - #lose ~= 10


class TimeConfig:
    def __init__(self):
        self.whole_move_num = 12
        self.endgame_move_num = 4
        self.decay_factor = 0.9
