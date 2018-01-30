from logging import getLogger
from time import sleep

import copy

from src.reversi_zero.config import Config
from src.reversi_zero.lib.pipe_helper import PipeFilesManager, reverse_in_out
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

logger = getLogger(__name__)


def start(config: Config):
    return VersusWorker(config).start()


class GameInfo:
    def __init__(self, index, process, p1_first, game_pipe_pair, result_pipe_pair):
        self.index = index
        self.process = process
        self.p1_first = p1_first
        self.game_pipe_pair = game_pipe_pair
        self.result_pipe_pair = result_pipe_pair


class VersusWorkerBase:
    def __init__(self, config):
        self.config = config
        assert len(self.config.opts.pipe_pairs) == 1
        self.parent_pipe_pairs = self.config.opts.pipe_pairs[0]
        self.pipe_files = PipeFilesManager.new_one(self.config)

        self.win_n, self.draw_n, self.lose_n = 0, 0, 0

    def start_model_serving_process(self, model_config_path, model_weight_path, pipe_pairs):
        cmd = build_child_cmd(type='model_serving', config=self.config, pipe_pairs=pipe_pairs)
        cmd.extend([
            '--model-config-path', model_config_path,
            '--model-weight-path', model_weight_path,
        ])
        return start_child_proc(cmd=cmd)

    def start_1_game_process(self, pps, p1_first):
        raise Exception('not implemented yet')

    def start_model_serving_processes(self, p1_model_ready_pp, p2_model_ready_pp, p1_model_pps, p2_model_pps):
        raise Exception('not implemented yet')

    def start(self):

        n_workers = self.config.opts.n_workers

        pipe_pairs = self.pipe_files.make_pipes(3 * n_workers + 2)

        p1_model_ready_pp = pipe_pairs[0]
        p2_model_ready_pp = pipe_pairs[1]
        pipe_pairs = pipe_pairs[2:]
        result_pps = pipe_pairs[:n_workers]
        p1_model_pps = pipe_pairs[n_workers:2*n_workers]
        p2_model_pps = pipe_pairs[2*n_workers:3*n_workers]

        self.start_model_serving_processes(p1_model_ready_pp, p2_model_ready_pp, p1_model_pps, p2_model_pps)

        game_info_list = [
            GameInfo(
                result_pipe_pair=result_pps[i].reverse_in_out(),
                game_pipe_pair=[result_pps[i], p1_model_pps[i], p2_model_pps[i]],
                index=None,
                process=None,
                p1_first=None
            ) for i in range(n_workers)
        ]

        unplayed_games = self.config.opts.n_games
        ongoing_games = 0
        game_index = 0
        while unplayed_games > 0 or ongoing_games > 0:
            for info in game_info_list:
                if not info.process and unplayed_games > 0:
                    info.index = game_index
                    info.p1_first = game_index % 2 == 0 if self.config.opts.p1_first is None \
                        else True if self.config.opts.p1_first == 'always' \
                        else False if self.config.opts.p1_first == 'never' \
                        else None
                    assert info.p1_first is not None, f'--p1-first could only be "always" or "never", or do not use it'
                    pps = copy.copy(info.game_pipe_pair)
                    info.process = self.start_1_game_process(pps, p1_first=info.p1_first)
                    info.result_pipe_pair.open_read_nonblock()
                    unplayed_games -= 1
                    game_index += 1
                    ongoing_games += 1
                elif info.process and info.process.poll() is not None:  # game process finished.
                    result = info.result_pipe_pair.read_no_empty().decode()

                    self.update_result(result)
                    logger.info(f'game #{info.index} : p1first:{1 if info.p1_first else 0}, result:{result:4}, '
                                f'{self.win_n} win, {self.draw_n} draw, {self.lose_n} lose')

                    ongoing_games -= 1
                    info.result_pipe_pair.close_read()
                    info.process = None
                    info.p1_first = None
                    info.index = None
                else:
                    sleep(1)

        if self.parent_pipe_pairs:
            self.parent_pipe_pairs.write_nonblock(f'{self.win_n},{self.draw_n},{self.lose_n}'.encode())
        else:
            logger.info(f"{self.win_n} wins, {self.draw_n} draws, {self.lose_n} loses")

        self.pipe_files.clear_pipes()

    def update_result(self, result):
        if result == 'win':
            self.win_n += 1
        elif result == 'lose':
            self.lose_n += 1
        elif result == 'draw':
            self.draw_n += 1
        else:
            raise Exception(f'unexpected return {result}')


class VersusWorker(VersusWorkerBase):
    def __init__(self, config):
        super().__init__(config)
        if self.config.opts.gpu_mem_frac is not None:
            self.config.opts.gpu_mem_frac /= 2

    def start_1_game_process(self, pps, p1_first):
        cmd = build_child_cmd(type='versus_a_game_kernel', config=self.config, pipe_pairs=pps)
        cmd.extend(['--p1-first', f'{p1_first}'])
        if self.config.opts.save_versus_dir:
            cmd.extend(["--save-versus-dir", self.config.opts.save_versus_dir])

        return start_child_proc(cmd=cmd, nocuda=True)

    def start_model_serving_processes(self, p1_model_ready_pp, p2_model_ready_pp, p1_model_pps, p2_model_pps):
        p1_model_ready_pp.open_read_nonblock()
        p2_model_ready_pp.open_read_nonblock()
        self.start_model_serving_process(self.config.opts.p1_model_config_path,
                                         self.config.opts.p1_model_weight_path,
                                         reverse_in_out([p1_model_ready_pp] + p1_model_pps))
        self.start_model_serving_process(self.config.opts.p2_model_config_path,
                                         self.config.opts.p2_model_weight_path,
                                         reverse_in_out([p2_model_ready_pp] + p2_model_pps))

        p1_model_ready_pp.read_no_empty(99, sleep_retry=0.1)  # having response means 'ready', whatever it is.
        p1_model_ready_pp.close_read()
        p2_model_ready_pp.read_no_empty(99, sleep_retry=0.1)  # having response means 'ready', whatever it is.
        p2_model_ready_pp.close_read()
