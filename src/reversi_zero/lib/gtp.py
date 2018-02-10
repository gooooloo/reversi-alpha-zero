# Most codes copied from https://github.com/jtauber/gtp

import re
from src.reversi_zero.lib.pipe_helper import PipePair


def pre_engine(s):
    s = re.sub("[^\t\n -~]", "", s)
    s = s.split("#")[0]
    s = s.replace("\t", " ")
    return s


def pre_controller(s):
    s = re.sub("[^\t\n -~]", "", s)
    s = s.replace("\t", " ")
    return s


def gtp_boolean(b):
    return "true" if b else "false"


def gtp_list(l):
    return "\n".join(l)


def gtp_color(color):
    # an arbitrary choice amongst a number of possibilities
    return {BLACK: "B", WHITE: "W"}[color]


def gtp_vertex(vertex):
    if vertex == PASS:
        return "pass"
    elif vertex == RESIGN:
        return "resign"
    else:
        x, y = vertex
        return "{}{}".format("ABCDEFGHJKLMNOPQRSTYVWYZ"[x - 1], y)


def gtp_move(color, vertex):
    return " ".join([gtp_color(color), gtp_vertex(vertex)])


def parse_message(message):
    message = pre_engine(message).strip()
    first, rest = (message.split(" ", 1) + [None])[:2]
    if first.isdigit():
        message_id = int(first)
        if rest is not None:
            command, arguments = (rest.split(" ", 1) + [None])[:2]
        else:
            command, arguments = None, None
    else:
        message_id = None
        command, arguments = first, rest

    return message_id, command, arguments


WHITE = -1
BLACK = +1
EMPTY = 0

PASS = (0, 0)
RESIGN = "resign"


def parse_color(color):
    if color.lower() in ["b", "black"]:
        return BLACK
    elif color.lower() in ["w", "white"]:
        return WHITE
    else:
        return False


def parse_vertex(vertex_string):
    if vertex_string is None:
        return False
    elif vertex_string.lower() == "pass":
        return PASS
    elif len(vertex_string) > 1:
        x = "abcdefghjklmnopqrstuvwxyz".find(vertex_string[0].lower()) + 1
        if x == 0:
            return False
        if vertex_string[1:].isdigit():
            y = int(vertex_string[1:])
        else:
            return False
    else:
        return False
    return (x, y)


def parse_move(move_string):
    color_string, vertex_string = (move_string.split(" ") + [None])[:2]
    color = parse_color(color_string)
    if color is False:
        return False
    vertex = parse_vertex(vertex_string)
    if vertex is False:
        return False

    return color, vertex


MIN_BOARD_SIZE = 7
MAX_BOARD_SIZE = 19


def format_success(message_id, response=None):
    if response is None:
        response = ""
    else:
        response = " {}".format(response)
    if message_id:
        return "={}{}\n".format(message_id, response)
    else:
        return "={}\n".format(response)


def format_error(message_id, response):
    if response:
        response = " {}".format(response)
    if message_id:
        return "?{}{}\n".format(message_id, response)
    else:
        return "?{}\n".format(response)


class GTPServer(object):

    def __init__(self, game_obj, name="gtp (python library)", version="0.2"):

        self.size = 19
        self.komi = 6.5

        self._game = game_obj
        self._game.clear()

        self._name = name
        self._version = version

        self.disconnect = False

        self.known_commands = [
            field[4:] for field in dir(self) if field.startswith("cmd_")]

    def cmd(self, message):
        message_id, command, arguments = parse_message(message)
        if command in self.known_commands:
            try:
                return format_success(
                    message_id, getattr(self, "cmd_" + command)(arguments))
            except ValueError as exception:
                return format_error(message_id, exception.args[0])
        else:
            return format_error(message_id, "unknown command")

    def vertex_in_range(self, vertex):
        if vertex == PASS:
            return True
        if 1 <= vertex[0] <= self.size and 1 <= vertex[1] <= self.size:
            return True
        else:
            return False

    # commands

    def cmd_protocol_version(self, arguments):
        return 2

    def cmd_name(self, arguments):
        return self._name

    def cmd_version(self, arguments):
        return self._version

    def cmd_known_command(self, arguments):
        return gtp_boolean(arguments in self.known_commands)

    def cmd_list_commands(self, arguments):
        return gtp_list(self.known_commands)

    def cmd_quit(self, arguments):
        self.disconnect = True
        return 'Done'

    def cmd_boardsize(self, arguments):
        if arguments.isdigit():
            size = int(arguments)
            if MIN_BOARD_SIZE <= size <= MAX_BOARD_SIZE:
                self.size = size
                self._game.set_size(size)
                return 'Done'
            else:
                raise ValueError("unacceptable size")
        else:
            raise ValueError("non digit size")

    def cmd_clear_board(self, arguments):
        self._game.clear()
        return 'Done'

    def cmd_komi(self, arguments):
        try:
            komi = float(arguments)
            self.komi = komi
            self._game.set_komi(komi)
        except ValueError:
            raise ValueError("syntax error")

    def cmd_play(self, arguments):
        move = parse_move(arguments)
        if move:
            color, vertex = move
            if self.vertex_in_range(vertex):
                if self._game.make_move(color, vertex):
                    return 'Done'
        raise ValueError("illegal move")

    def cmd_genmove(self, arguments):
        c = parse_color(arguments)
        if c:
            move = self._game.get_move(c)
            self._game.make_move(c, move)
            return gtp_vertex(move)
        else:
            raise ValueError("unknown player: {}".format(arguments))

    def cmd_is_over(self, arguments):
        return self._game.is_over()

    def cmd_final_score(self, arguments):
        return self._game.final_score()


class GTPClient(object):

    def __init__(self, pipe_pair: PipePair):
        self.pipe_pair = pipe_pair

    def send(self, data):
        self.pipe_pair.open_write_block()
        self.pipe_pair.write(data.encode())
        self.pipe_pair.close_write()

        self.pipe_pair.open_read_nonblock()
        while True:
            data = self.pipe_pair.try_read_allow_empty()
            if data and len(data):
                result = data.decode().strip()
                if len(result) > 0:
                    break
        self.pipe_pair.close_read()
        return result

    def name(self):
        self.send("name")

    def version(self):
        self.send("version")

    def boardsize(self, boardsize):
        self.send("boardsize {}".format(boardsize))

    def komi(self, komi):
        self.send("komi {}".format(komi))

    def clear_board(self):
        self.send("clear_board")

    def genmove(self, color):
        message = self.send(
            "genmove {}".format(gtp_color(color)))
        assert message[0] == "=", message
        return parse_vertex(message[1:].strip())

    def showboard(self):
        self.send("showboard")

    def play(self, color, vertex):
        self.send("play {}".format(gtp_move(color, vertex)))

    def is_over(self):
        message = self.send("is_over")
        assert message[0] == "=", message
        return message[1:].strip() == 'True'

    def final_score(self):
        message = self.send("final_score")
        assert message[0] == "=", message
        score_string = message[1:].strip()
        assert score_string[0] == '('
        assert score_string[-1] == ')'
        score_string = score_string[1:-1]
        scores = score_string.split(',')
        assert len(scores) == 2
        return int(scores[0].strip()), int(scores[1].strip())
