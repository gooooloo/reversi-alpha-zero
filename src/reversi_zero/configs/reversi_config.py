# the 'AZ' in comments means 'AlphaZero'
# the 'AGZ' in comments means 'AlphaGoZero'
# the 'MOKE' in comments means @mokemokechicken's implementation


class PlayDataConfig:
    def __init__(self):
        # AGZ paper says: "... from the most recent 500,000 games of self-play.
        # But I reduce to nb_game_in_file * max_file_num == 50,000 due to performance trade-off.
        # Small nb_game_in_file make training data update more frequently, but
        # large max_file_num make larger overhead reading file
        self.nb_game_in_file = 5            # MOKE: 5
        self.max_file_num = 10000           # MOKE: 2000


class PlayConfig:
    def __init__(self):
        self.simulation_num_per_move = 800  # AZ:800, AGZ:1600,     MOKE: 400
        self.c_puct = 5                     # AZ: same,             MOKE: 1
        self.noise_eps = 0.25               # AZ: same,             MOKE: same
        self.dirichlet_alpha = 0.4          # AZ: depends on game,  MOKE: 0.5
        self.change_tau_turn = 10           # AZ: 30,               MOKE: same
        self.virtual_loss = 3               # AZ: same,             MOKE: same
        self.prediction_queue_size = 8      # AZ: 8,                MOKE: 16
        self.parallel_search_num = 8        # AZ: N/A,              MOKE: same
        self.prediction_worker_sleep_sec  = 0.0001
        self.wait_for_expanding_sleep_sec = 0.00001
        self.can_resign = True
        self.v_resign_check_min_n = 100
        self.v_resign_init = -0.9           # AZ: UNKNOWN,          MOKE: same
        self.v_resign_delta = 0.01          # AZ: UNKNOWN,          MOKE: same
        self.v_resign_disable_prop = 0.1    # AZ: same,             MOKE: same
        self.v_resign_false_positive_fraction_t_max = 0.05  # AZ: same, MOKE: same
        # If we don't have a min fraction, then we may have a lower frac, in worst case we will have NO
        # resignation. Than means we will have to train many 1-side games. Not what we want.
        self.v_resign_false_positive_fraction_t_min = 0.04  # AZ: UNKNOWN, MOKE: N/A
        self.n_games_to_self_play = 999999999
        self.render = False


class TrainerConfig:
    def __init__(self):
        self.batch_size = 3072             # AZ: 4096 - I don't have so much GPU memory though, MOKE: 512
        self.epoch_to_checkpoint = 1
        self.start_total_steps = 0
        self.epoch_steps = 100              # AZ: 1?                                            MOKE: 200~9000
        # AZ paper says "maintains a single NN that is update continually". That means save_model_steps = 1?
        # However in practice, we want to balance something...
        self.save_model_steps = 800         # AZ: 1?                                            MOKE: 200~9000
        self.generation_model_steps = 800   # AZ: N/A.                                          MOKE: N/A
        self.min_data_size_to_learn = 12500 # AZ: N/A                                           MOKE: same
        self.lr_schedule = (  # (learning rate, before step count) # AZ: schedule UNKNOWN       MOKE: (0.01,100k),(0.001,200k),(0.0001,~)
            (0.2,    1500),
            (0.02,   20000),
            (0.002,  100000),
            (0.0002, 9999999999)
        )
        self.need_eval = False


class ModelConfig:
    cnn_filter_num = 256
    cnn_filter_size = 3
    res_layer_num = 10
    l2_reg = 1e-4
    value_fc_size = 256
    input_size = (5,8,8)    # AZ: (17,8,8),   MOKE:(3,8,8)
    policy_size = 8*8+1


class PlayWithHumanConfig:
    def __init__(self):
        self.noise_eps = 0
        self.change_tau_turn = 0

    def update_play_config(self, pc):
        pc.noise_eps = self.noise_eps
        pc.change_tau_turn = self.change_tau_turn


class EnvSpecificConfig:
    def __init__(self):
        self.env_arg_name = "reversi"
        self.env_module_name = "reversi_zero.env.reversi_env"
        self.env_class_name = "ReversiEnv"
        self.board_edge_size = 8


class GuiConfig:
    def __init__(self):
        self.window_size = (400, 440)
        self.window_title = "reversi-alpha-zero"
        self.EDGE_LENGTH = 8
        self.x_is_vertical = False


class EvalConfig:
    def __init__(self):
        self.elo_k = 32
        self.n_games = 400
        self.elo_threshold = 150


class TimeConfig:
    def __init__(self):
        self.whole_move_num = 60
        self.endgame_move_num = 20
        self.decay_factor = 0.9
