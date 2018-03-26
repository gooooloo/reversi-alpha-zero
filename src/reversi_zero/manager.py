import argparse
import json
import os
from logging import getLogger

from .config import Config, Options
from .lib.logger import setup_logger
from .lib.pipe_helper import load_pipe_pairs_names

logger = getLogger(__name__)

CMD_LIST = [
    # train
    'init',  # Model init.
    'eval',  # Evaluator, only for AlphaGoZero way. GPU required.
    'fs',    # File server. CPU only.
    'opt',   # training model, GPU required.
    'self',  # self play, GPU required.

    # play
    'elo_p1',
    'elo_p1_ntest',
    'league'
    'play_gui',
    'http_server',

    # internal
    'gtp_server',
    'gtp_server_ntest',
    'model_serving',
    'model_cache',
    'self_play_kernel',
    'versus_a_game_kernel',
    'versus_a_game_kernel_ntest',
    'versus_n_games',
    'versus_n_games_ntest',
]


def str2bool(v):
    # https://stackoverflow.com/a/43357954
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", help="what to do", choices=CMD_LIST)
    parser.add_argument("--ask-model", help="", type=str2bool, default=False)
    parser.add_argument("--can-resign", help="if player can resign when self play", type=str2bool, default=True)
    parser.add_argument("--config-file", help="", default=None)
    parser.add_argument("--elo-k", help="", type=int, default=32)
    parser.add_argument("--env", help="which env to train", default="reversi")
    parser.add_argument("--gpu-mem-frac", help="gpu memory fraction", default=None)
    parser.add_argument("--http-port", help="", type=int, default=8888)
    parser.add_argument("--http-server-type", help="", default=None)
    parser.add_argument("--http-url", help="", default='localhost')
    parser.add_argument("--league-result", help="",  default='./league-result.txt')
    parser.add_argument("--model-cache-size", help="", type=int, default=None)
    parser.add_argument("--model-config-path", help="model-config-path", default=None)
    parser.add_argument("--model-serving-step-check", help="", type=int, default=None)
    parser.add_argument("--model-weight-path", help="model-weight-path", default=None)
    parser.add_argument("--n-games", help="how many games to self play", type=int, default=1)
    parser.add_argument("--n-minutes", help="how many minutes per game per player", type=int, default=None)
    parser.add_argument("--n-sims", help="how many simulations per move", type=int, default=None)
    parser.add_argument("--n-steps-model", help="which model( after how many training steps) to play", type=int, default=-1)
    parser.add_argument("--n-workers", help="how many processes as workers", type=int, default=1)
    parser.add_argument("--need-eval", help="tell opt new model needs evaluation. 'opt' cmd only", type=str2bool, default=False)
    parser.add_argument("--ntest-depth", help="",  type=int, default=1)
    parser.add_argument("--p1-elo", help="", type=int, default=0)
    parser.add_argument("--p1-first", help="", default=None)
    parser.add_argument("--p1-model-config-path", help="p1-model-config-path", default=None)
    parser.add_argument("--p1-model-weight-path", help="p1-model-weight-path", default=None)
    parser.add_argument("--p1-n-sims", help="how many simulations per move for p1", type=int, default=None)
    parser.add_argument("--p1-name", help="p1-name", default=None)
    parser.add_argument("--p2-elo", help="", type=int, default=0)
    parser.add_argument("--p2-model-config-path", help="p2-model-config-path", default=None)
    parser.add_argument("--p2-model-weight-path", help="p2-model-weight-path", default=None)
    parser.add_argument("--p2-n-sims", help="how many simulations per move for p2", type=int, default=None)
    parser.add_argument("--p2-name", help="p2-name", default=None)
    parser.add_argument("--pipes", help="", default=None)
    parser.add_argument("--render", help="if render in console when self play", type=str2bool, default=False)
    parser.add_argument("--save-versus-dir", help="", default=None)
    parser.add_argument("--total-step", help="set TrainerConfig.start_total_steps", type=int)
    return parser


def args_to_opts(args):
    opts = Options()

    if args.config_file is not None:
        with open(args.config_file, 'rt') as f:
            d = json.load(f)
            for k,v in d.items():
                if v is not None and hasattr(opts, k):
                    setattr(opts, k, v)

    # overwrite what was set from config_file
    if args.ask_model is not None: opts.ask_model = args.ask_model
    if args.can_resign is not None: opts.can_resign = args.can_resign
    if args.cmd is not None: opts.cmd = args.cmd
    if args.elo_k is not None: opts.elo_k = args.elo_k
    if args.env is not None: opts.env = args.env
    if args.http_port is not None: opts.http_port = args.http_port
    if args.http_server_type is not None: opts.http_server_type = args.http_server_type
    if args.http_url is not None: opts.http_url = args.http_url
    if args.league_result is not None: opts.league_result = args.league_result
    if args.model_cache_size is not None: opts.model_cache_size = args.model_cache_size
    if args.model_config_path is not None: opts.model_config_path = args.model_config_path
    if args.model_serving_step_check is not None: opts.model_serving_step_check = args.model_serving_step_check
    if args.model_weight_path is not None: opts.model_weight_path = args.model_weight_path
    if args.n_games is not None: opts.n_games = args.n_games
    if args.n_minutes is not None: opts.n_minutes = args.n_minutes
    if args.n_sims is not None: opts.n_sims = args.n_sims
    if args.n_steps_model is not None: opts.n_steps_model = args.n_steps_model
    if args.n_workers is not None: opts.n_workers = args.n_workers
    if args.need_eval is not None: opts.need_eval = args.need_eval
    if args.ntest_depth is not None: opts.ntest_depth = args.ntest_depth
    if args.p1_elo is not None: opts.p1_elo = args.p1_elo
    if args.p1_model_config_path is not None: opts.p1_model_config_path = args.p1_model_config_path
    if args.p1_model_weight_path is not None: opts.p1_model_weight_path = args.p1_model_weight_path
    if args.p1_n_sims is not None: opts.p1_n_sims = args.p1_n_sims
    if args.p1_name is not None: opts.p1_name = args.p1_name
    if args.p2_elo is not None: opts.p2_elo = args.p2_elo
    if args.p2_model_config_path is not None: opts.p2_model_config_path = args.p2_model_config_path
    if args.p2_model_weight_path is not None: opts.p2_model_weight_path = args.p2_model_weight_path
    if args.p2_n_sims is not None: opts.p2_n_sims = args.p2_n_sims
    if args.p2_name is not None: opts.p2_name = args.p2_name
    if args.pipes is not None: opts.pipe_pairs = load_pipe_pairs_names(args.pipes)
    if args.render is not None: opts.render = args.render
    if args.save_versus_dir is not None: opts.save_versus_dir = args.save_versus_dir
    if args.total_step is not None: opts.start_total_steps = args.total_step

    if args.gpu_mem_frac is not None:
        try: opts.gpu_mem_frac = float(args.gpu_mem_frac)
        except ValueError: pass
    if args.p1_first is not None:
        if args.p1_first in ('always', 'never'):
            opts.p1_first = args.p1_first
        else:
            opts.p1_first = str2bool(args.p1_first)

    return opts


def setup(config: Config, setup_logger_flag):
    if config.opts.n_steps_model >= 0:
        model_dir = os.path.join(config.resource.generation_model_dir, config.resource.generation_model_dirname_tmpl % config.opts.n_steps_model)
        config.resource.model_config_path = os.path.join(model_dir, config.resource.model_config_filename)
        config.resource.model_weight_path = os.path.join(model_dir, config.resource.model_weight_filename)

    if config.opts.start_total_steps is not None:
        config.trainer.start_total_steps = config.opts.start_total_steps

    if config.opts.model_config_path is not None:
        config.resource.model_config_path = config.opts.model_config_path
    if config.opts.model_weight_path is not None:
        config.resource.model_weight_path = config.opts.model_weight_path
    config.resource.create_directories()

    if setup_logger_flag:
        setup_logger(config.resource.main_log_path)

    config.trainer.need_eval = config.opts.need_eval

    if config.opts.can_resign is not None:
        config.play.can_resign = config.opts.can_resign
    if config.opts.render is not None:
        config.play.render = config.opts.render
    if config.opts.n_sims is not None:
        config.play.simulation_num_per_move = config.opts.n_sims

    if config.opts.model_cache_size is not None:
        config.model_cache.model_cache_size = config.opts.model_cache_size


def start():

    parser = create_parser()
    args = parser.parse_args()

    opts = args_to_opts(args)

    config = Config(opts)
    setup_logger_flag = args.cmd != 'play_gui'
    setup(config,setup_logger_flag=setup_logger_flag)

    if args.cmd == 'init':
        from src.reversi_zero.worker.train import init_model as worker
    elif args.cmd == "self":
        from src.reversi_zero.worker.train import self_play as worker
    elif args.cmd == 'opt':
        from src.reversi_zero.worker.train import optimize as worker
    elif args.cmd == 'eval':
        from src.reversi_zero.worker.train import evaluate as worker
    elif args.cmd == 'fs':
        from src.reversi_zero.worker.train import fs as worker

    elif args.cmd == 'play_gui':
        from src.reversi_zero.worker.play import gui as worker
    elif args.cmd == 'elo_p1':
        from src.reversi_zero.worker.play import elo_p1 as worker
    elif args.cmd == 'league':
        from src.reversi_zero.worker.play import league as worker
    elif args.cmd == 'elo_p1_ntest':
        from src.reversi_zero.worker.play import elo_p1_ntest as worker
    elif args.cmd == 'http_server':
        from src.reversi_zero.worker.play import http_server as worker

    elif args.cmd == 'model_serving':
        from src.reversi_zero.worker.internal import model_serving as worker
    elif args.cmd == 'model_cache':
        from src.reversi_zero.worker.internal import model_cache as worker
    elif args.cmd == 'self_play_kernel':
        from src.reversi_zero.worker.internal import self_play_kernel as worker
    elif args.cmd == 'versus_a_game_kernel':
        from src.reversi_zero.worker.internal import versus_a_game_kernel as worker
    elif args.cmd == 'versus_n_games':
        from src.reversi_zero.worker.internal import versus_n_games as worker
    elif args.cmd == 'gtp_server':
        from src.reversi_zero.worker.internal import gtp_server as worker
    elif args.cmd == 'versus_a_game_kernel_ntest':
        from src.reversi_zero.worker.internal import versus_a_game_kernel_ntest as worker
    elif args.cmd == 'versus_n_games_ntest':
        from src.reversi_zero.worker.internal import versus_n_games_ntest as worker
    elif args.cmd == 'gtp_server_ntest':
        from src.reversi_zero.worker.internal import gtp_server_ntest as worker

    else:
        raise Exception(f'unsupported cmd {args.cmd}')

    return worker.start(config)

