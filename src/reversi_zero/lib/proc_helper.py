import os
import signal
import subprocess
import sys

from src.reversi_zero.lib.pipe_helper import dump_pipe_pairs_names


children_processes = []
exit_tasks = []


def build_child_cmd(type, opts, pipe_pairs):

    tmp_config_file_path = f'/tmp/reresi_alpha_zero/{config.env.env_class_name}/' \
                           f'config_{time.time()}_{random.randint(100000, 999999)}.json'

    def remove_tmp_config_file(*args):
        import os
        os.unlink(tmp_config_file_path)
    add_exit_task(remove_tmp_config_file)

    with open(tmp_config_file_path, 'wt') as f:
        import json
        json.dump(f, opts.__dict__)

    cmd = ['python3.6', '-m', 'src.reversi_zero.run', type,
           '--pipe', dump_pipe_pairs_names(pipe_pairs),
           '--config-file', tmp_config_file_path
           ]

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
