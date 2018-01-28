import json
import operator

from src.reversi_zero.lib import elo as elo_lib
from logging import getLogger

import time

from src.reversi_zero.config import Config
from src.reversi_zero.lib import elo as elo_lib
from src.reversi_zero.lib.pipe_helper import PipeFilesManager, reverse_in_out
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

logger = getLogger(__name__)


def start(config):
    return LeagueWorker(config).start()

from collections import namedtuple
Player = namedtuple('Player', 'name, config weight n_sims')


def get_player(generation, n_sims):
    return Player(
        name=f'{generation}_{n_sims}',
        config=f'/fds/exp/alpha-zero/reversi/data/model/generation_models/model_{generation}-steps/model_config.json',
        weight=f'/fds/exp/alpha-zero/reversi/data/model/generation_models/model_{generation}-steps/model_weight.h5',
        n_sims=n_sims
    )

PLAYERS = [
    # get_player(0, 100),
    # get_player(0, 800),
    # get_player(0, 2000),
    # get_player(56800, 100),
    # get_player(56800, 800),
    # get_player(56800, 2000),
    # get_player(116000, 100),
    # get_player(116000, 800),
    # get_player(116000, 2000),
    # get_player(200800, 100),
    # get_player(200800, 800),
    # get_player(200800, 2000),
    # get_player(263200, 100),
    # get_player(263200, 800),
    # get_player(263200, 2000),
    # get_player(302400, 40),
    # get_player(302400, 100),
    # get_player(302400, 800),
    # get_player(302400, 2000),
    # get_player(304800, 40),
    # get_player(304800, 100),
    # get_player(304800, 800),
    # get_player(304800, 2000),
    # get_player(312000, 40),
    # get_player(312000, 100),
    # get_player(312000, 800),
    # get_player(312000, 2000),
    # get_player(314400, 40),
    # get_player(314400, 100),
    # get_player(314400, 400),
    # get_player(314400, 800),
    # get_player(314400, 2000),
    # get_player(336000, 40),
    # get_player(336000, 100),
    # get_player(336000, 400),
    get_player(350400, 40),
    get_player(350400, 100),
    get_player(350400, 400),
    # get_player(360000, 40),
    # get_player(360000, 100),
    # get_player(360000, 400),
    get_player(386400, 40),
    get_player(386400, 100),
    get_player(386400, 400),
    get_player(391200, 40),
    get_player(391200, 100),
    get_player(391200, 400),
]


class LeagueWorker:
    def __init__(self, config: Config):
        self.config = config
        self.players = PLAYERS
        self.pipe_files = PipeFilesManager.new_one(self.config)
        self.n_games = 4
        self.result_file = self.config.opts.league_result

    def start(self):
        import itertools
        games = itertools.combinations(reversed(self.players), 2)
        results = {}
        try:
            import os
            if os.path.exists(self.result_file):
                with open(self.result_file, 'rt') as f:
                    results = json.load(f)
        except Exception as e:
            logger.debug(e)

        self.print_result(results)
        for p1, p2 in games:
            if not p1.name < p2.name:
                p1, p2 = p2, p1
            key = f'{p1.name}_vs_{p2.name}'
            if key in results:
                continue
            logger.info(key)
            r = self.vs(p1, p2, self.n_games)
            results[key] = r

            self.print_result(results)
            with open(self.result_file, 'wt') as f:
                json.dump(results, f)

        limited_results = {}
        names = [p.name for p in self.players]
        for k in results:
            p1, p2 = k.split('_vs_')
            if p1 in names and p2 in names:
                limited_results[k] = results[k]
        results = limited_results

        elo = {}
        expected = {}
        actual = {}
        for k in results:
            p1, p2 = k.split('_vs_')
            elo[p1] = 0
            elo[p2] = 0
            expected[p1] = 0
            expected[p2] = 0
            actual[p1] = 0
            actual[p2] = 0

        for k in results:
            p1, p2 = k.split('_vs_')
            w,d,l = int(results[k][0]), int(results[k][1]), int(results[k][2])

            expected[p1] += elo_lib.expected(elo[p1], elo[p2]) * (w+d+l)
            expected[p2] += elo_lib.expected(elo[p2], elo[p1]) * (w+d+l)
            actual[p1] += w+d*0.5
            actual[p2] += l+d*0.5

        for p in elo:
            elo[p] = elo_lib.elo(elo[p], expected[p], actual[p], self.config.opts.elo_k)

        self.print_result(results)
        self.print_elo(elo)


    @staticmethod
    def print_elo(elo):
        logger.info('===========ELO==============')
        elo = [x for x in reversed(sorted(elo.items(), key=operator.itemgetter(1)))]
        for k in elo:
            logger.info(f'{k[0]:15} : {k[1]}')
        logger.info('============================')

    @staticmethod
    def print_result(result):
        logger.info('=========VS RESULTS=========')
        for k in result:
            logger.info(f'{k:30} : {result[k]}')
        logger.info('============================')

    def vs(self, player1 : Player, player2 : Player, n_games):

        pipe_pairs = self.pipe_files.make_pipes(1)
        cmd = build_child_cmd(type='versus_n_games', config=self.config, pipe_pairs=reverse_in_out(pipe_pairs))
        cmd.extend([
            '--n-games', f'{n_games}',
            '--n-workers', f'{self.config.opts.n_workers}',
            '--p1-n-sims', f'{player1.n_sims}',
            "--p1-model-config-path", player1.config,
            "--p1-model-weight-path", player1.weight,
            '--p2-n-sims', f'{player2.n_sims}',
            "--p2-model-config-path", player2.config,
            "--p2-model-weight-path", player2.weight,
        ])

        pipe_pairs[0].open_read_nonblock()
        p = start_child_proc(cmd=cmd).wait()

        result = pipe_pairs[0].read_no_empty()
        assert result
        result = result.decode()
        result = result.split(',')
        result = [int(x) for x in result]

        pipe_pairs[0].close_read()
        self.pipe_files.clear_pipes()

        return result


