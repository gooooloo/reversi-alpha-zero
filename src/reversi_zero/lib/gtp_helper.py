import time

from src.reversi_zero.agent.player import EvaluatePlayer
from src.reversi_zero.env.ienv import IEnv
from src.reversi_zero.lib.pipe_helper import PipePair

CMD_CLEAR_BOARD = 1
CMD_THINK = 2
CMD_PLAY = 3


class GTPServer(object):

    def __init__(self, env: IEnv, player: EvaluatePlayer, pipe_pair: PipePair):

        self.pipe_pair = pipe_pair
        self._env = env
        self._player = player

    def start(self):
        self.pipe_pair.open_read_nonblock()
        while True:
            cmd = self.pipe_pair.read_int(allow_empty=True)
            if cmd is None:
                time.sleep(0.1)
            elif cmd == CMD_CLEAR_BOARD:
                self._env.reset()
                self._player.prepare(self._env)
            elif cmd == CMD_PLAY:
                action = self.pipe_pair.read_int(allow_empty=False)
                self._env.step(action)
                self._player.play(action, self.env)
            elif cmd == CMD_THINK:
                action, _, _ = self._player.think()
                self.pipe_pair.open_write_block()
                self.pipe_pair.write_int(action)
                self.pipe_pair.close_write()
            else:
                raise Exception("bad cmd " + cmd)


class GTPClient(object):

    def __init__(self, pipe_pair: PipePair):
        self.pipe_pair = pipe_pair

    def clear_board(self):
        self.pipe_pair.open_write_block()
        self.pipe_pair.write_int(CMD_CLEAR_BOARD)
        self.pipe_pair.close_write()

    def think(self):
        self.pipe_pair.open_read_nonblock()

        self.pipe_pair.open_write_block()
        self.pipe_pair.write_int(CMD_THINK)
        self.pipe_pair.close_write()

        ret = self.pipe_pair.read_int(allow_empty=False)
        self.pipe_pair.close_read()

        return ret

    def play(self, action):
        self.pipe_pair.open_write_block()
        self.pipe_pair.write_int(CMD_PLAY)
        self.pipe_pair.write_int(action)
        self.pipe_pair.close_write()
