import argparse
import json
from logging import getLogger

from .config import Config, Options
from .lib.logger import setup_logger
from .lib.pipe_helper import load_pipe_pairs_names

logger = getLogger(__name__)

CMD_LIST = [
    # train
    'init',  # Model init.
    'fs',    # File server. CPU only.
    'opt',   # training model, GPU required.
    'self',  # self eval, GPU required.
    'eval',  # Evaluator, only for AlphaGoZero way. GPU required.

    # internal
    'gtp_server',
    'model_serving',
    'model_cache',
    'self_play_kernel',
    'versus_a_game_kernel',
    'versus_n_games',
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
    parser.add_argument("--can-resign", help="if player can resign when self eval", type=str2bool, default=True)
    parser.add_argument("--config-file", help="", default=None)
    parser.add_argument("--dir", help="", default=None)
    parser.add_argument("--env", help="which env to train", default="reversi")
    parser.add_argument("--fs-ip", help="", default='localhost')
    parser.add_argument("--fs-port", help="", type=int, default=8888)
    parser.add_argument("--gpu-mem-frac", help="gpu memory fraction", default=None)
    parser.add_argument("--model-cache-size", help="", type=int, default=None)
    parser.add_argument("--model-step", help="", default=None)
    parser.add_argument("--n-games", help="how many games to self eval", type=int, default=99999999999)
    parser.add_argument("--n-sims", help="how many simulations per move", type=int, default=None)
    parser.add_argument("--n-workers", help="how many processes as workers", type=int, default=1)
    parser.add_argument("--need-eval", help="tell opt new model needs evaluation. 'opt' cmd only", type=str2bool, default=False)
    parser.add_argument("--p1-first", help="", default=None)
    parser.add_argument("--p1-model-step", help="p1-model-step", default=None)
    parser.add_argument("--p2-model-step", help="p2-model-step", default=None)
    parser.add_argument("--pipe-pairs", help="", default=None)
    parser.add_argument("--start-total-steps", help="set TrainerConfig.start_total_steps", type=int)
    return parser


def args_to_opts(args):
    opts = Options()

    if args.can_resign is not None: opts.can_resign = args.can_resign
    if args.cmd is not None: opts.cmd = args.cmd
    if args.dir is not None: opts.dir = args.dir
    if args.env is not None: opts.env = args.env
    if args.fs_ip is not None: opts.fs_ip = args.fs_ip
    if args.fs_port is not None: opts.fs_port = args.fs_port
    if args.model_cache_size is not None: opts.model_cache_size = args.model_cache_size
    if args.model_step is not None: opts.model_step = args.model_step
    if args.n_games is not None: opts.n_games = args.n_games
    if args.n_sims is not None: opts.n_sims = args.n_sims
    if args.n_workers is not None: opts.n_workers = args.n_workers
    if args.need_eval is not None: opts.need_eval = args.need_eval
    if args.p1_model_step is not None: opts.p1_model_step = args.p1_model_step
    if args.p2_model_step is not None: opts.p2_model_step = args.p2_model_step
    if args.pipe_pairs is not None: opts.pipe_pairs = args.pipe_pairs
    if args.start_total_steps is not None: opts.start_total_steps = args.start_total_steps

    if args.gpu_mem_frac is not None:
        try: opts.gpu_mem_frac = float(args.gpu_mem_frac)
        except ValueError: pass
    if args.p1_first is not None:
        if args.p1_first in ('always', 'never'):
            opts.p1_first = args.p1_first
        else:
            opts.p1_first = str2bool(args.p1_first)

    # overwrite what was set from config_file
    if args.config_file is not None:
        with open(args.config_file, 'rt') as f:
            d = json.load(f)
            for k,v in d.items():
                if v is not None and hasattr(opts, k):
                    setattr(opts, k, v)
    return opts


def setup(config: Config):

    if config.opts.start_total_steps is not None:
        config.trainer.start_total_steps = config.opts.start_total_steps

    config.resource.create_directories()

    setup_logger(config.resource.main_log_path)

    config.trainer.need_eval = config.opts.need_eval

    if config.opts.can_resign is not None:
        config.play.can_resign = config.opts.can_resign
    if config.opts.n_sims is not None:
        config.play.simulation_num_per_move = config.opts.n_sims

    if config.opts.model_cache_size is not None:
        config.model_cache.model_cache_size = config.opts.model_cache_size

    if config.opts.gpu_mem_frac is not None:
        config.gpu.gpu_mem_frac = config.opts.gpu_mem_frac

    if config.opts.fs_ip is not None:
        config.ipc.fs_ip = config.opts.fs_ip
    if config.opts.fs_port is not None:
        config.ipc.fs_port = config.opts.fs_port
    if config.opts.pipe_pairs is not None:
        config.ipc.pipe_pairs = load_pipe_pairs_names(config.opts.pipe_pairs)
    if config.opts.n_workers is not None:
        config.ipc.n_workers = config.opts.n_workers

    if config.opts.n_games is not None:
        config.eval.n_games = config.opts.n_games
    if config.opts.p1_first is not None:
        config.eval.p1_first = config.opts.p1_first
    if config.opts.p1_model_step is not None:
        config.eval.p1_model_step = config.opts.p1_model_step
    if config.opts.p2_model_step is not None:
        config.eval.p2_model_step = config.opts.p2_model_step

    if config.opts.model_step is not None:
        config.model.model_step = config.opts.model_step


def start():

    parser = create_parser()
    args = parser.parse_args()

    opts = args_to_opts(args)

    config = Config(opts)
    setup(config)

    if args.cmd == 'init':
        from src.reversi_zero.worker.train import init_model as worker
    elif args.cmd == "self":
        from src.reversi_zero.worker.train import self_play as worker
    elif args.cmd == 'opt':
        from src.reversi_zero.worker.train import optimize as worker
    elif args.cmd == 'fs':
        from src.reversi_zero.worker.train import fs as worker

    elif args.cmd == 'model_serving':
        from src.reversi_zero.worker.train import model_serving as worker
    elif args.cmd == 'model_cache':
        from src.reversi_zero.worker.train import model_cache as worker
    elif args.cmd == 'self_play_kernel':
        from src.reversi_zero.worker.train import self_play_kernel as worker

    elif args.cmd == 'eval':
        from src.reversi_zero.worker.eval import evaluate as worker

    elif args.cmd == 'versus_a_game_kernel':
        from src.reversi_zero.worker.eval import versus_a_game_kernel as worker
    elif args.cmd == 'versus_n_games':
        from src.reversi_zero.worker.eval import versus_n_games as worker
    elif args.cmd == 'gtp_server':
        from src.reversi_zero.worker.eval import gtp_server as worker

    else:
        raise Exception(f'unsupported cmd {args.cmd}')

    return worker.start(config)

