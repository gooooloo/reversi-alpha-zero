import re
from logging import getLogger, WARNING
from subprocess import PIPE

from src.reversi_zero.lib import gtp
from src.reversi_zero.lib.gtp import gtp_vertex, parse_vertex
from src.reversi_zero.lib.proc_helper import start_child_proc

logger = getLogger()
logger.setLevel(WARNING)

PASS_B = 'PA'
PASS_VERTEX = gtp.PASS


def v_2_b(vertex):
    if vertex == PASS_VERTEX:
        return PASS_B
    return gtp_vertex(vertex)


def b_2_v(b):
    if b == PASS_B:
        return PASS_VERTEX

    return parse_vertex(b)


class GTPNBoardGameObj(object):
    def __init__(self, cmd, cwd, depth):
        self.size = 8
        self.depth = depth
        self.cmd = cmd
        self.cwd = cwd
        self.p = None

        self.ping_index = 0

    def send(self, cmd, answer_pattern=None):
        assert self.p
        logger.debug(f'===input: {cmd}')
        cmd = cmd+'\n'
        cmd = cmd.encode()
        self.p.stdin.write(cmd)
        self.p.stdin.flush()

        answer = None
        if answer_pattern:
            p = re.compile(answer_pattern)
            while True:
                line = self.p.stdout.readline().decode()
                if line[-1] == '\n':
                    line = line[:-1]
                if p.match(line):
                    answer = line
                    logger.debug(f'===answer: {answer}')
                    break

        return answer

    def clear(self):
        if not self.p:
            self.p = start_child_proc(cmd=self.cmd, nocuda=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=self.cwd)
            self.send('nboard 2')
            self.send(f'set depth {self.depth}')

        cmd = 'set game (;' \
              'GM[Othello]' \
              'PC[NBoard]' \
              'DT[2014-02-21 20:52:27 GMT]' \
              'PB[?]' \
              'PW[?]' \
              'RE[?]' \
              'TI[15:00]' \
              'TY[8]' \
              'BO[8 ---------------------------*O------O*--------------------------- *]' \
              ';)'
        self.send(cmd)

    def make_move(self, color, vertex):
        return self.send(f'move {v_2_b(vertex)}')

    def get_move(self, color):
        self.ping()
        move = self.send('go', answer_pattern=f'=== ([ABCDEFGH][12345678]|{PASS_B}).*')
        move = move[4:6]

        v = b_2_v(move)
        return v

    def ping(self):
        self.ping_index += 1
        self.send(f'ping {self.ping_index}', f'^pong {self.ping_index}$')

    def is_over(self):
        raise Exception('dont call')

    def final_score(self):
        raise Exception('dont call')
