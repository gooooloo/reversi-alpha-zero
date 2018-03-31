
import os
import sys

_PATH_ = os.path.dirname(os.path.dirname(__file__))

if _PATH_ not in sys.path:
    sys.path.append(_PATH_)


if __name__ == "__main__":

    from src.reversi_zero.lib.proc_helper import kill_children_processes, add_exit_task, signal_exit
    add_exit_task(kill_children_processes)
    signal_exit()

    from src.reversi_zero import manager
    try:
        manager.start()
    finally:
        kill_children_processes()
