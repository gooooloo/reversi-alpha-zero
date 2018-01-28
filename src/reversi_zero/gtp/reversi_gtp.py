from src.reversi_zero.lib.gtp import GTPServer


class ReversiGTPServer(GTPServer):
    def __init__(self, game_obj):
        super().__init__(game_obj)

        self.size = game_obj.size

        self.known_commands.remove('komi')
        self.known_commands.remove('boardsize')

    def cmd_boardsize(self, arguments):
        raise ValueError("not supported")

    def cmd_komi(self, arguments):
        raise ValueError("not supported")
