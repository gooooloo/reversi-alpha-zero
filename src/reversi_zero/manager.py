import argparse
import os
from logging import getLogger

from .config import Config
from .lib.logger import setup_logger
from .lib.pipe_helper import load_pipe_pairs_names

logger = getLogger(__name__)

CMD_LIST = [
    'elo_p1',
    'elo_p1_ntest',
    'eval',
    'gtp_server',
    'gtp_server_ntest',
    'http_server',
    'model_serving',
    'opt',
    'play_gui',
    'res',
    'self',
    'self_play_kernel',
    'versus_a_game_kernel',
    'versus_a_game_kernel_ntest',
    'versus_n_games',
    'versus_n_games_ntest',
    'league'
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
    parser.add_argument("--total-step", help="set TrainerConfig.start_total_steps", type=int)
    parser.add_argument("--gpu-mem-frac", help="gpu memory fraction", default=None)
    parser.add_argument("--model-config-path", help="model-config-path", default=None)
    parser.add_argument("--model-weight-path", help="model-weight-path", default=None)
    parser.add_argument("--p1-model-config-path", help="p1-model-config-path", default=None)
    parser.add_argument("--p1-model-weight-path", help="p1-model-weight-path", default=None)
    parser.add_argument("--p2-model-config-path", help="p2-model-config-path", default=None)
    parser.add_argument("--p2-model-weight-path", help="p2-model-weight-path", default=None)
    parser.add_argument("--env", help="which env to train", default="reversi")
    parser.add_argument("--n-games", help="how many games to self play", type=int, default=1)
    parser.add_argument("--n-workers", help="how many processes as workers", type=int, default=1)
    parser.add_argument("--n-sims", help="how many simulations per move", type=int, default=None)
    parser.add_argument("--n-steps-model", help="which model( after how many training steps) to play", type=int, default=-1)
    parser.add_argument("--p1-n-sims", help="how many simulations per move for p1", type=int, default=None)
    parser.add_argument("--p2-n-sims", help="how many simulations per move for p2", type=int, default=None)
    parser.add_argument("--p1-first", help="", default=None)
    parser.add_argument("--need-eval", help="tell opt new model needs evaluation. 'opt' cmd only", type=str2bool, default=False)
    parser.add_argument("--can-resign", help="if player can resign when self play", type=str2bool, default=True)
    parser.add_argument("--render", help="if render in console when self play", type=str2bool, default=False)
    parser.add_argument("--pipes", help="", default=None)
    parser.add_argument("--p1-elo", help="", type=int, default=0)
    parser.add_argument("--p2-elo", help="", type=int, default=0)
    parser.add_argument("--elo-k", help="", type=int, default=32)
    parser.add_argument("--http-port", help="", type=int, default=8888)
    parser.add_argument("--http-url", help="", default=None)
    parser.add_argument("--ask-model", help="", type=str2bool, default=False)
    parser.add_argument("--league-result", help="",  default='./league-result.txt')
    parser.add_argument("--ntest-depth", help="",  type=int, default=1)
    parser.add_argument("--save-versus-dir", help="", default=None)
    parser.add_argument("--p1-name", help="p1-name", default=None)
    parser.add_argument("--p2-name", help="p2-name", default=None)
    return parser


def setup(config: Config, args, setup_logger_flag):
    config.opts.n_workers = args.n_workers
    config.opts.n_games = args.n_games
    if args.gpu_mem_frac is not None:
        try: config.opts.gpu_mem_frac = float(args.gpu_mem_frac)
        except ValueError: pass
    if args.pipes is not None:
        config.opts.pipe_pairs = load_pipe_pairs_names(args.pipes)
    if args.p1_model_config_path is not None:
        config.opts.p1_model_config_path = args.p1_model_config_path
    if args.p1_model_weight_path is not None:
        config.opts.p1_model_weight_path = args.p1_model_weight_path
    if args.p2_model_config_path is not None:
        config.opts.p2_model_config_path = args.p2_model_config_path
    if args.p2_model_weight_path is not None:
        config.opts.p2_model_weight_path = args.p2_model_weight_path
    if args.p1_elo is not None:
        config.opts.p1_elo = args.p1_elo
    if args.p2_elo is not None:
        config.opts.p2_elo = args.p2_elo
    if args.elo_k is not None:
        config.opts.elo_k = args.elo_k
    config.opts.http_url = args.http_url
    config.opts.http_port = args.http_port
    config.opts.ask_model = args.ask_model
    if args.p1_n_sims is not None:
        config.opts.p1_n_sims = args.p1_n_sims
    if args.p2_n_sims is not None:
        config.opts.p2_n_sims = args.p2_n_sims
    config.opts.league_result = args.league_result
    if args.p1_first:
        if args.p1_first in ('always', 'never'):
            config.opts.p1_first = args.p1_first
        else:
            config.opts.p1_first = str2bool(args.p1_first)
    config.opts.ntest_depth = args.ntest_depth
    config.opts.save_versus_dir = args.save_versus_dir
    config.opts.p1_name = args.p1_name
    config.opts.p2_name = args.p2_name
    if args.n_steps_model >= 0:
        model_dir = os.path.join(config.resource.generation_model_dir, config.resource.generation_model_dirname_tmpl % args.n_steps_model)
        config.resource.model_config_path = os.path.join(model_dir, config.resource.model_config_filename)
        config.resource.model_weight_path = os.path.join(model_dir, config.resource.model_weight_filename)

    if args.total_step is not None:
        config.trainer.start_total_steps = args.total_step

    if args.model_config_path is not None:
        config.resource.model_config_path = args.model_config_path
    if args.model_weight_path is not None:
        config.resource.model_weight_path = args.model_weight_path
    config.resource.create_directories()

    if setup_logger_flag:
        setup_logger(config.resource.main_log_path)

    config.trainer.need_eval = args.need_eval

    if args.can_resign is not None:
        config.play.can_resign = args.can_resign
    if args.render is not None:
        config.play.render = args.render
    if args.n_sims is not None:
        config.play.simulation_num_per_move = args.n_sims


def start():

    parser = create_parser()
    args = parser.parse_args()

    config = Config(args.env)
    setup_logger_flag = args.cmd != 'play_gui'
    setup(config, args, setup_logger_flag=setup_logger_flag)

    if args.cmd == "self":
        from .worker import self_play as worker
    elif args.cmd == 'opt':
        from .worker import optimize as worker
    elif args.cmd == 'eval':
        from .worker import evaluate as worker
    elif args.cmd == 'play_gui':
        from .play_game import gui as worker
    elif args.cmd == 'elo_p1':
        from .worker import elo_p1 as worker
    elif args.cmd == 'res':
        from .worker import resignation as worker
    elif args.cmd == 'model_serving':
        from .worker import model_serving as worker
    elif args.cmd == 'self_play_kernel':
        from .worker import self_play_kernel as worker
    elif args.cmd == 'versus_a_game_kernel':
        from .worker import versus_a_game_kernel as worker
    elif args.cmd == 'versus_n_games':
        from .worker import versus_n_games as worker
    elif args.cmd == 'gtp_server':
        from .worker import gtp_server as worker
    elif args.cmd == 'http_server':
        from .worker import http_server as worker
    elif args.cmd == 'league':
        from .worker import league as worker
    elif args.cmd == 'elo_p1_ntest':
        from .worker import elo_p1_ntest as worker
    elif args.cmd == 'versus_a_game_kernel_ntest':
        from .worker import versus_a_game_kernel_ntest as worker
    elif args.cmd == 'versus_n_games_ntest':
        from .worker import versus_n_games_ntest as worker
    elif args.cmd == 'gtp_server_ntest':
        from .worker import gtp_server_ntest as worker
    else:
        raise Exception(f'unsupported cmd {args.cmd}')

    return worker.start(config)

