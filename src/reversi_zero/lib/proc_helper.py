import os
import signal
import subprocess
import sys

from src.reversi_zero.lib.pipe_helper import dump_pipe_pairs_names


children_processes = []
exit_tasks = []


def build_child_cmd(type, config, pipe_pairs):
    cmd = ['python3.6', '-m', 'src.reversi_zero.run', type,
           '--env', f'{config.env.env_arg_name}',
           '--n-sims', f'{config.play.simulation_num_per_move}',
           '--pipe', dump_pipe_pairs_names(pipe_pairs),
           ]
    if config.opts.gpu_mem_frac is not None:
        cmd.append('--gpu-mem-frac')
        cmd.append(f'{config.opts.gpu_mem_frac}')

    return cmd


def start_child_proc(cmd, nocuda=None, stdin=None, stdout=None, stderr=None, cwd=None):
    global children_processes

    env = os.environ.copy()
    if nocuda:
        env['CUDA_VISIBLE_DEVICES'] = ''

    try:
        p = subprocess.Popen(cmd, env=env, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd)
    except Exception:
        print(cmd)
        raise

    children_processes.append(p)

    return p


def kill_children_processes(*args):
    for p in children_processes:
        if p and p.poll() is None:
            p.kill()


def add_exit_task(task):
    global exit_tasks
    exit_tasks.append(task)


def clean(*args):
    for t in exit_tasks:
        print(t)
        t(*args)
    sys.exit()


def signal_exit():
    for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
        signal.signal(sig, clean)
