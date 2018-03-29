import os
from datetime import datetime

from src.reversi_zero.env.reversi.lib.nboard import v_2_b
from src.reversi_zero.lib import gtp


class GGF:
    def __init__(self, black_name, white_name):
        self.black_name = black_name
        self.white_name = white_name
        self.black_score = None
        self.white_score = None
        self.moves = ''

    def play(self, color, vertex):
        v = v_2_b(vertex)
        s = 'B' if color == gtp.BLACK else 'W'
        self.moves += f'{s}[{v}]'

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
