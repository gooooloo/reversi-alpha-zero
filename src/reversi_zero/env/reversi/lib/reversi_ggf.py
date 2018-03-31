import os
from datetime import datetime

from src.reversi_zero.env.reversi.lib.nboard import v_2_b

from src.reversi_zero.lib import ggf
from src.reversi_zero.lib.ggf import GGF


class ReversiGGF(GGF):
    def __init__(self):
        self.black_name = 'black'
        self.white_name = 'white'
        self.black_score = None
        self.white_score = None
        self.moves = ''

    def set_black_name(self, black_name):
        self.black_name = black_name

    def set_white_name(self, white_name):
        self.white_name = white_name

    def play(self, color, vertex):
        color = 'B' if isinstance(color, ggf.BLACK) else 'W'
        v = v_2_b(vertex)
        self.moves += f'{color}[{v}]'

    def write_to_file(self, dir):
        time = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        string = f'(;' \
                 f'GM[Othello]' \
                 f'PC[RAZ]' \
                 f'DT[{time}]' \
                 f'PB[{self.black_name}]' \
                 f'PW[{self.white_name}]' \
                 f'RE[{self.black_score}{self.white_score}]' \
                 f'TY[8]' \
                 f'BO[8 ---------------------------*O------O*--------------------------- *                     ]' \
                 f'{self.moves}' \
                 f';)'

        filename = f'reversi-' \
                   f'{self.black_name}-' \
                   f'{self.white_name}-' \
                   f'{self.black_score}_{self.white_score}-' \
                   f'{time}.ggf'
        filename = filename.replace(':', '_')
        filename = os.path.join(dir,filename)
        with open(filename, 'wt') as f:
            f.write(string)

    def set_final_score(self, final_score):
        self.black_score, self.white_score = [int(x) for x in final_score]

    def get_result(self):
        if self.black_score == self.white_score:
            return 'draw'
        if self.black_score > self.white_score:
            return 'bwin'
        if self.black_score < self.white_score:
            return 'blose'
        raise Exception('wrong')
