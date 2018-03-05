import enum
from logging import getLogger
import importlib

from collections import namedtuple

from src.reversi_zero.agent.player import EvaluatePlayer
from src.reversi_zero.config import Config
from src.reversi_zero.lib import gtp
from src.reversi_zero.lib.gtp import GTPClient, WHITE, BLACK
from src.reversi_zero.lib.http import HttpPlayClient
from src.reversi_zero.lib.pipe_helper import PipeFilesManager
from src.reversi_zero.lib.proc_helper import build_child_cmd, start_child_proc

LastHistory = namedtuple('LastHistory', 'Q N V P')

logger = getLogger(__name__)

GameEvent = enum.Enum("GameEvent", "update ai_move over pass")

Player = enum.Enum("Player", "black white")

class PlayWithHuman:
    def __init__(self, config: Config):
        self.config = config
        self.human_color = None
        self.ai_color = None
        self.observers = []
        class_attr = getattr(importlib.import_module(config.env.env_module_name), config.env.env_class_name)
        self.env = class_attr()
        self.env.reset()
        self.ai = None  # type: EvaluatePlayer
        self.ai_confidence = None
        self.action_pass = self.config.env.board_edge_size * self.config.env.board_edge_size

        if not self.config.opts.http_url:
            pipe_files = PipeFilesManager.new_one(self.config)
            pipe_pairs = pipe_files.make_pipes(1)

            pipe_pairs[0].open_read_nonblock()
            self.start_http_server_process([pipe_pairs[0].reverse_in_out()], self.config.opts.http_port)
            pipe_pairs[0].read_no_empty(99, sleep_retry=0.1)  # having response means 'ready', whatever it is.
            pipe_pairs[0].close_read()

            url = f'http://localhost:{self.config.opts.http_port}'

        else:
            url = self.config.opts.http_url

        self.http_client = HttpPlayClient(url)
        self.next_color = None

    def start_http_server_process(self, pipe_pairs, port):
        cmd = build_child_cmd(type='http_server', config=self.config, pipe_pairs=pipe_pairs)
        cmd.extend([
            '--http-port', f'{port}',
            '--model-config-path', self.config.resource.model_config_path,
            '--model-weight-path', self.config.resource.model_weight_path,
        ])
        return start_child_proc(cmd=cmd, nocuda=True)

    def add_observer(self, observer_func):
        self.observers.append(observer_func)

    def notify_all(self, event):
        for ob_func in self.observers:
            ob_func(event)

    def start_game(self, human_is_black):
        self.human_color = BLACK if human_is_black else WHITE
        self.ai_color = WHITE if human_is_black else BLACK
        self.next_color = BLACK

        self.env.reset()
        self.http_client.clear_board()
        self.ai_confidence = None

    def next_is_human(self):
        return self.next_color == self.human_color

    def play_next_turn(self):
        self.notify_all(GameEvent.update)

        if self.over:
            self.notify_all(GameEvent.over)
            return

        if not self.next_is_human():
            self.notify_all(GameEvent.ai_move)

        if self.does_human_can_only_pass():
            self.env.step(self.action_pass)
            self.http_client.play(self.human_color, gtp.PASS)
            self.next_color = self.ai_color
            self.notify_all(GameEvent.ai_move)

    @property
    def over(self):
        return self.env.done

    @property
    def next_player(self):
        return self.env.next_player

    def stone(self, px, py):
        r = self.env.color_of_vertex(px, py)
        return r

    @property
    def number_of_black_and_white(self):
        return self.env.score

    def available(self, px, py):
        pos = int(py * self.config.gui.EDGE_LENGTH + px)
        return self.env.is_legal(pos)

    def does_human_can_only_pass(self):
        if not self.next_is_human():
            return False

        # TODO
        lm = [i for i,l in enumerate(self.env.legal_moves) if l == 1]
        return len(lm) == 1 and lm[0] == self.action_pass

    def move(self, px, py):

        if not self.next_is_human():
            raise Exception('not human\'s turn!')

        self.http_client.play(self.human_color, (px+1, py+1))
        self.env.step(py*self.config.env.board_edge_size+px)
        self.next_color = self.ai_color

    def move_by_ai(self):
        if self.next_is_human():
            raise Exception('not AI\'s turn!')

        print('start thinking...')
        vertex = self.http_client.genmove(self.ai_color)
        action = self.v_2_a(vertex)
        print('end thinking...')
        self.env.step(action)
        self.next_color = self.human_color

        # N, Q, V, P = self.ai.get_think_info()
        # self.ai_confidence = vs
        # self.last_history = LastHistory(Q, N, V, P)

    def v_2_a(self, vertex):
        if vertex == gtp.PASS:
            return self.action_pass
        (x, y) = vertex
        return (y - 1) * self.config.env.board_edge_size + (x - 1)

