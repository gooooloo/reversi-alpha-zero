import os
from datetime import datetime

from src.reversi_zero.lib import gtp
from src.reversi_zero.lib.nboard import v_2_b


class GGF:
    def __init__(self, black_name, white_name):
        self.black_name = black_name
        self.white_name = white_name
        self.moves = ''

    def play(self, color, vertex):
        v = v_2_b(vertex)
        s = 'B' if color == gtp.BLACK else 'W'
        self.moves += f'{s}[{v}]'

    def write_to_file(self, dir):
        time = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
        string = f'(;' \
                 f'GM[Othello]PC[NBoard]' \
                 f'DT[time]' \
                 f'PB[{self.black_name}]PW[{self.white_name}]' \
                 f'RE[42]' \
                 f'TI[55:00]' \
                 f'TY[8]' \
                 f'BO[8 ---------------------------*O------O*--------------------------- *                     ]' \
                 f'{self.moves}' \
                 f';)'

        filename = os.path.join(dir, f'reversi-{time}.ggf')
        with open(filename, 'wt') as f:
            f.write(string)
