import copy
from collections import deque
from logging import getLogger

import numpy as np

logger = getLogger(__name__)

EMPTY = 0
BLACK = 1
WHITE = 2
BLACK_AND_WHITE = 3

EMPTY_CHAR = ' '
BLACK_CHAR = 'O'
WHITE_CHAR = 'X'
CHARS = (EMPTY_CHAR, BLACK_CHAR, WHITE_CHAR)
EDGE_CHAR = '#'


def another_player(player):
    assert player == BLACK or player == WHITE
    return BLACK_AND_WHITE - player


def different_players(p1, p2):
    return p1 + p2 == BLACK_AND_WHITE


def same_players(p1, p2):
    return p1 == p2


class ReversiGenericEnv:
    def __init__(self, edge_size, board_history_max_len):

        self.EDGE_SIZE = edge_size
        assert self.EDGE_SIZE % 2 == 0

        self.BOARD_SIZE = self.EDGE_SIZE * self.EDGE_SIZE
        self.ACTION_PASS = self.BOARD_SIZE

        self.BOARD_HISTORY_MAX_LEN = board_history_max_len
        self.DIRECTIONS = ((1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1))

        self.board = None
        self.count = None
        self.black_count = None
        self.white_count = None
        self._legal_moves = None
        self.next_player = None
        self.turn = None
        self.done = None
        self.winner = None
        self._board_history = None

    def reset(self):

        self.board = [ [EMPTY for _ in range(self.EDGE_SIZE)] for _ in range(self.EDGE_SIZE)]

        self.board[self.EDGE_SIZE//2-1][self.EDGE_SIZE//2-1] = WHITE
        self.board[self.EDGE_SIZE//2][self.EDGE_SIZE//2] = WHITE
        self.board[self.EDGE_SIZE//2-1][self.EDGE_SIZE//2] = BLACK
        self.board[self.EDGE_SIZE//2][self.EDGE_SIZE//2-1] = BLACK

        self.count = [2, 2]

        self._legal_moves = None

        self.next_player = BLACK

        self.turn = 0
        self.done = False
        self.winner = None

        self._board_history = deque(maxlen=self.BOARD_HISTORY_MAX_LEN)
        for _ in range(self._board_history.maxlen):
            self._board_history.append(copy.copy(self.board))

    def copy(self):
        return copy.deepcopy(self)

    @property
    def last_player(self):
        return another_player(self.next_player)

    @property
    def last_player_wins(self):
        return self.done and self.winner == self.last_player

    @property
    def last_player_loses(self):
        return self.done and self.winner == another_player(self.last_player)

    @property
    def black_wins(self):
        return self.done and self.winner == BLACK

    @property
    def black_loses(self):
        return self.done and self.winner == WHITE

    @property
    def next_is_black(self):
        return self.next_player == BLACK

    def color_of_vertex(self, r, c):
        if self.board[r][c] == BLACK:
            return 'black'
        elif self.board[r][c] == WHITE:
            return 'white'
        else:
            return None

    def _vertex_to_action(self, r, c):
        return r*self.EDGE_SIZE + c

    def _action_to_vertex(self, a):
        return a//self.EDGE_SIZE,  a%self.EDGE_SIZE

    def _inside(self, r, c):
        return 0<=r<self.EDGE_SIZE and 0<=c<self.EDGE_SIZE

    def _is_legal(self, player, r, c):
        b = self.board

        if b[r][c] != EMPTY:
            return False

        for delta in self.DIRECTIONS:
            nr = r + delta[0]
            nc = c + delta[1]
            while self._inside(nr, nc) and different_players(player, b[nr][nc]):
                nr = nr + delta[0]
                nc = nc + delta[1]
            if nr==r+delta[0] and nc==c+delta[1]:
                # indicates neighbor in this direction is self or empty
                continue
            if self._inside(nr, nc) and same_players(player, b[nr][nc]):
                return True

        return False

    @property
    def legal_moves(self):
        if self._legal_moves is not None:
            return self._legal_moves

        can_pass = 1
        self._legal_moves = np.zeros([self.BOARD_SIZE+1], dtype=np.uint8)
        for r in range(self.EDGE_SIZE):
            for c in range(self.EDGE_SIZE):
                il = self._is_legal(self.next_player, r, c)
                self._legal_moves[self._vertex_to_action(r, c)] = 1 if il else 0
                if il:
                    can_pass = 0

        self._legal_moves[self.ACTION_PASS] = can_pass

        return self._legal_moves

    def is_legal(self, action):
        return self.legal_moves[action] == 1

    def equals(self, r):
        raise Exception("don't call")

    def step(self, action):
        assert 0 <= action <= self.ACTION_PASS, f"Illegal action={action}"

        assert self.is_legal(action)

        if action != self.ACTION_PASS:

            b = self.board
            r,c = self._action_to_vertex(action)
            assert b[r][c] == EMPTY

            b[r][c] = self.next_player
            self.count[self.next_player-1] += 1
            for delta in self.DIRECTIONS:
                nr = r + delta[0]
                nc = c + delta[1]
                while self._inside(nr, nc) and different_players(b[r][c], b[nr][nc]):
                    nr += delta[0]
                    nc += delta[1]
                if self._inside(nr, nc) and same_players(b[r][c], b[nr][nc]):
                    nr -= delta[0]
                    nc -= delta[1]
                    while self._inside(nr, nc) and different_players(b[r][c], b[nr][nc]):
                        b[nr][nc] = b[r][c]
                        self.count[self.next_player-1] += 1
                        self.count[another_player(self.next_player)-1] -= 1
                        nr -= delta[0]
                        nc -= delta[1]

        self._legal_moves = None
        self._board_history.append(self.board.copy())
        self.turn += 1
        self.next_player = another_player(self.next_player)

        if self._should_game_over():
            self._game_over()

        return self.board, {}

    def _should_game_over(self,):

        if self.count[0] + self.count[1] >= self.BOARD_SIZE:
            return True

        if not self.is_legal(self.ACTION_PASS):
            return False

        # now next_player can only pass. Check next_next_player...
        p = another_player(self.next_player)
        for r in range(self.EDGE_SIZE):
            for c in range(self.EDGE_SIZE):
                if self._is_legal(p, r, c):
                    return False

        return True

    def _game_over(self):
        self.done = True
        if self.winner is None:
            black_num, white_num = self.count[BLACK-1], self.count[WHITE-1]
            if black_num > white_num:
                self.winner = BLACK
            elif black_num < white_num:
                self.winner = WHITE
            else:
                self.winner = None

    def resign(self):
        self.winner = another_player(self.next_player)
        self._game_over()

    def render(self):
        b, w = self.score
        print(f"next={'black' if self.next_player == BLACK else 'white'} turn={self.turn} b{b} w{w}")

        s = EDGE_CHAR*(self.EDGE_SIZE+2) + "\n"
        for r in range(self.EDGE_SIZE):
            s += EDGE_CHAR
            for c in range(self.EDGE_SIZE):
                s += CHARS[self.board[r][c]]
            s += EDGE_CHAR
            s += "\n"
        s += EDGE_CHAR*(self.EDGE_SIZE+2)

        print(s)

    @property
    def score(self):
        return self.count[BLACK-1], self.count[WHITE-1]

    @property
    def observation(self):
        ob = np.zeros([1+2*self._board_history.maxlen, self.EDGE_SIZE, self.EDGE_SIZE])

        own = self.next_player
        enemy = another_player(self.next_player)
        for i,b in enumerate(reversed(self._board_history)):
            for r in range(self.EDGE_SIZE):
                for c in range(self.EDGE_SIZE):
                    if b[r][c] == own:
                        ob[2*i][r][c] = 1
                    elif b[r][c] == enemy:
                        ob[2*i+1][r][c] = 1
                    else:
                        pass

        if own == BLACK:
            ob[-1] = np.ones([self.EDGE_SIZE, self.EDGE_SIZE])

        return ob


    def compress_ob(self, ob):
        if self.BOARD_SIZE <= 16:
            dtype = np.uint16
        elif self.BOARD_SIZE <= 64:
            dtype = np.uint64
        else:
            raise Exception("not supported yet!")

        cob = np.ndarray([len(ob)], dtype=dtype)
        for idx,plane in enumerate(ob):
            x = 0
            for y in plane.reshape(self.BOARD_SIZE):
                x <<= 1
                x |= int(y)

            cob[idx] = x

        return cob

    def decompress_ob(self, cob):
        ob = np.ndarray([len(cob), self.EDGE_SIZE, self.EDGE_SIZE], dtype=np.uint8)
        for idx,plane in enumerate(cob):
            ob[idx] = np.array(list(format(plane, 'b').zfill(self.BOARD_SIZE)), dtype=np.uint8).reshape(self.EDGE_SIZE,self.EDGE_SIZE)

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
        assert x.shape == (1+2*self.BOARD_HISTORY_MAX_LEN, self.EDGE_SIZE, self.EDGE_SIZE), f'{x.shape}'
        if is_flip_vertical > 0:
            x = np.flip(x, axis=1)
        if rotate_right_num > 0:
            x = np.rot90(x, rotate_right_num, axes=(1,2))
        return x

    def rotate_flip_pi(self, pi, op):
        assert len(pi) == 1+self.BOARD_SIZE, f'{pi}'
        assert isinstance(op, int)
        assert 0 <= op < 8

        is_flip_vertical = op % 2
        rotate_right_num = op % 4
        if is_flip_vertical == 0 and rotate_right_num == 0:
            return pi

        # we dont handle the "PASS" action
        part_pi = np.asarray(pi[:-1]).reshape(self.EDGE_SIZE, self.EDGE_SIZE)
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
        assert len(pi) == 1+self.BOARD_SIZE, f'{pi}'
        assert isinstance(op, int)
        assert 0 <= op < 8

        is_flip_vertical = op % 2
        rotate_right_num = op % 4
        if is_flip_vertical == 0 and rotate_right_num == 0:
            return pi

        # we dont handle the "PASS" action
        part_pi = np.asarray(pi[:-1]).reshape(self.EDGE_SIZE, self.EDGE_SIZE)
        # to make part_pi same dim as ob when counter rotate flip
        part_pi = part_pi[None]
        if rotate_right_num > 0:
            part_pi = np.rot90(part_pi, rotate_right_num, axes=(2, 1))
        if is_flip_vertical > 0:
            part_pi = np.flip(part_pi, axis=1)

        new_pi = np.append(part_pi[0], pi[-1])
        assert len(new_pi) == len(pi)
        return new_pi


class Reversi4x4Env(ReversiGenericEnv):
    def __init__(self):
        super(Reversi4x4Env, self).__init__(edge_size=4, board_history_max_len=1)

class Reversi6x6Env(ReversiGenericEnv):
    def __init__(self):
        super(Reversi6x6Env, self).__init__(edge_size=6, board_history_max_len=2)
