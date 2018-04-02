import enum
from collections import deque
from logging import getLogger

import numpy as np

from src.reversi_zero.env.ienv import IEnv
from src.reversi_zero.env.reversi.lib.bitboard import board_to_string, calc_flip, bit_count, find_correct_moves, bit_to_array

logger = getLogger(__name__)
# noinspection PyArgumentList
Player = enum.Enum("Player", "black white")


def another_player(player):
    if player is None:
        raise Exception('do not call when player is none. Maybe you forget to call reset()?')
    return Player.white if player == Player.black else Player.black


class ReversiEnv(IEnv):
    def __init__(self):

        self.board = None
        self.next_player = None  # type: Player
        self.turn = 0
        self._done = False
        self.winner = None  # type: Player
        self._board_history = deque(maxlen=2)
        for _ in range(self._board_history.maxlen):
            self._board_history.append(self.board)

    def reset(self):
        self.board = Board()
        self.next_player = Player.black
        self.turn = 0
        self._done = False
        self.winner = None
        self._board_history.clear()
        for _ in range(self._board_history.maxlen):
            self._board_history.append(self.board.copy() if self.board is not None else None)
        return self

    def copy(self):
        ret = ReversiEnv()
        ret.board = self.board.copy() if self.board is not None else None
        ret.next_player = self.next_player
        ret.turn = self.turn
        ret._done = self._done
        ret.winner = self.winner
        ret._board_history = deque(maxlen=self._board_history.maxlen)
        for i in self._board_history:
            ret._board_history.append(i.copy() if i is not None else None)
        return ret

    @property
    def last_player(self):
        return another_player(self.next_player)

    @property
    def last_player_wins(self):
        return self._done and self.winner == self.last_player

    @property
    def last_player_loses(self):
        return self._done and self.winner == another_player(self.last_player)

    @property
    def black_wins(self):
        return self._done and self.winner == Player.black

    @property
    def black_loses(self):
        return self._done and self.winner == another_player(Player.black)

    @property
    def legal_moves(self):
        own, enemy = self.get_own_and_enemy()
        bit = find_correct_moves(own, enemy)
        array = bit_to_array(bit, 64)
        array = np.append(array, 1 if bit == 0 else 0)  # if no correct move, then you can pass
        assert np.sum(array) > 0
        return array

    def is_legal(self, action):
        return self.legal_moves[action] == 1

    def equals(self, r):
        return self.board.equals(r.board) and \
               self.next_player == r.next_player and \
               self.turn == r.turn and \
               self._done == r._done and \
               self.winner == r.winner and \
               self._board_history.equals(r._board_history)

    def step(self, action):
        """

        :param int action: move pos=0 ~ 64 (0=top left, 7 top right, 63 bottom right, 64 pass)
        :return:
        """
        assert 0 <= action <= 64, f"Illegal action={action}"
        action_pass = 64

        if action != action_pass:
            own, enemy = self.get_own_and_enemy()

            assert own & (1 << action) == 0, f'{own}, {action}'
            assert enemy & (1 << action) == 0, f'{enemy}, {action}'

            flipped = calc_flip(action, own, enemy)
            if bit_count(flipped) == 0:
                raise Exception(f'{self.next_player} played illegal move to lose in turn {self.turn}!')
                print()
                self._board_history.append(self.board.copy())
                self.turn += 1
                self.change_to_next_player()
                self.illegal_move_to_lose(action)
                return self.board, {}
            own ^= flipped
            own |= 1 << action
            enemy ^= flipped

            self.set_own_and_enemy(own, enemy)

        self._board_history.append(self.board.copy())
        self.turn += 1
        self.change_to_next_player()

        if self._should_game_over():
            self._game_over()

        return self.board, {}

    def _should_game_over(self,):
        own, enemy = self.get_own_and_enemy()

        if bit_count(enemy) + bit_count(own) >= 64:
            return True
        else:
            return bit_count(find_correct_moves(enemy, own)) == 0 and \
                   bit_count(find_correct_moves(own, enemy)) == 0

    @property
    def done(self):
        return self._done

    def _game_over(self):
        self._done = True
        if self.winner is None:
            black_num, white_num = self.board.number_of_black_and_white
            if black_num > white_num:
                self.winner = Player.black
            elif black_num < white_num:
                self.winner = Player.white
            else:
                self.winner = None

    def change_to_next_player(self):
        self.next_player = another_player(self.next_player)

    def illegal_move_to_lose(self, action):
        logger.warning(f"Illegal action={action}, No Flipped!")
        self.winner = another_player(self.next_player)
        self._game_over()

    def resign(self):
        self.winner = another_player(self.next_player)
        self._game_over()

    def get_own_and_enemy(self):
        if self.next_player == Player.black:
            own, enemy = self.board.black, self.board.white
        else:
            own, enemy = self.board.white, self.board.black
        return own, enemy

    def set_own_and_enemy(self, own, enemy):
        if self.next_player == Player.black:
            self.board.black, self.board.white = own, enemy
        else:
            self.board.white, self.board.black = own, enemy

    def render(self):
        b, w = self.board.number_of_black_and_white
        print(f"next={self.next_player.name} turn={self.turn} B={b}({int(self.board.black)}) W={w}({int(self.board.white)})")
        print(board_to_string(self.board.black, self.board.white, with_edge=True))

    @property
    def score(self):
        return self.board.number_of_black_and_white

    def color_of_vertex(self, r, c):
        pos = r*8+c
        if self.board.black & (1<<pos):
            return 'black'
        elif self.board.white & (1<<pos):
            return 'white'
        else:
            return None

    @property
    def observation(self):
        ob = np.ndarray([1+2*self._board_history.maxlen, 8, 8])
        if self.next_player == Player.black:
            for i,b in enumerate(reversed(self._board_history)):
                ob[2*i] = bit_to_array(b.black, 64).reshape(8, 8)
                ob[2*i+1] = bit_to_array(b.white, 64).reshape(8, 8)
            ob[-1] = np.ones([8, 8])
        else:
            for i,b in enumerate(reversed(self._board_history)):
                ob[2*i] = bit_to_array(b.white, 64).reshape(8, 8)
                ob[2*i+1] = bit_to_array(b.black, 64).reshape(8, 8)
            ob[-1] = np.zeros([8, 8])

        return ob


    @property
    def cob_dtype(self):
        return np.uint64

    def compress_ob(self, ob):
        cob = np.ndarray([len(ob)], dtype=np.uint64)
        for idx,plane in enumerate(ob):
            x = 0
            for y in plane.reshape(64):
                x <<= 1
                x |= int(y)

            cob[idx] = x

        return cob

    def decompress_ob(self, cob):

        ob = np.ndarray([len(cob), 8, 8], dtype=np.uint8)
        for idx,plane in enumerate(cob):
            ob[idx] = np.array(list(format(plane, 'b').zfill(64)), dtype=np.uint8).reshape(8,8)

        return ob


    @property
    def rotate_flip_op_count(self):
        return 8

    def rotate_flip_ob(self, ob, op):
        # (di(p), v) = fθ(di(sL))
        # rotation and flip. flip -> rot.
        assert isinstance(op, int)
        assert 0 <= op < 8
        is_flip_vertical = op % 2
        rotate_right_num = op % 4
        x = ob
        assert x.shape == (1+2*self._board_history.maxlen, 8, 8), f'{x.shape}'
        if is_flip_vertical > 0:
            x = np.flip(x, axis=1)
        if rotate_right_num > 0:
            x = np.rot90(x, rotate_right_num, axes=(1,2))
        return x

    def rotate_flip_pi(self, pi, op):
        assert len(pi) == 65, f'{pi}'
        assert isinstance(op, int)
        assert 0 <= op < 8

        is_flip_vertical = op % 2
        rotate_right_num = op % 4
        if is_flip_vertical == 0 and rotate_right_num == 0:
            return pi

        # we dont handle the "PASS" action
        part_pi = np.asarray(pi[:-1]).reshape(8, 8)
        # to make part_pi same dim as ob when counter rotate flip
        part_pi = part_pi[None]
        if is_flip_vertical > 0:
            part_pi = np.flip(part_pi, axis=1)
        if rotate_right_num > 0:
            part_pi = np.rot90(part_pi, rotate_right_num, axes=(1, 2))

        new_pi = np.append(part_pi[0], pi[-1])
        assert len(new_pi) == len(pi)
        return new_pi

    def counter_rotate_flip_pi(self, pi, op):
        assert len(pi) == 65, f'{pi}'
        assert isinstance(op, int)
        assert 0 <= op < 8

        is_flip_vertical = op % 2
        rotate_right_num = op % 4
        if is_flip_vertical == 0 and rotate_right_num == 0:
            return pi

        # we dont handle the "PASS" action
        part_pi = np.asarray(pi[:-1]).reshape(8, 8)
        # to make part_pi same dim as ob when counter rotate flip
        part_pi = part_pi[None]
        if rotate_right_num > 0:
            part_pi = np.rot90(part_pi, rotate_right_num, axes=(2, 1))
        if is_flip_vertical > 0:
            part_pi = np.flip(part_pi, axis=1)

        new_pi = np.append(part_pi[0], pi[-1])
        assert len(new_pi) == len(pi)
        return new_pi


class Board:
    def __init__(self, black=None, white=None, init_type=0):
        self.black = int(black or (0b00001000 << 24 | 0b00010000 << 32))
        self.white = int(white or (0b00010000 << 24 | 0b00001000 << 32))

        if init_type:
            self.black, self.white = self.white, self.black

    def equals(self, b):
        return self.black == b.black and self.white == b.white

    def copy(self):
        return Board(self.black, self.white)

    @property
    def number_of_black_and_white(self):
        return bit_count(self.black), bit_count(self.white)

