
class TimeStrategy:
    def __init__(self, minutes_per_game, whole_move_num, endgame_move_num, decay_factor):
        self.seconds_per_game = 60 * minutes_per_game
        self.whole_move_num = whole_move_num
        self.endgame_move_num = endgame_move_num
        self.decay_factor = decay_factor

        self.move_num = 0

    def play(self):
        self.move_num += 1

    def get_seconds_for_thinking(self):
        return time_recommendation(move_num=self.move_num,
                                   whole_move_num=self.whole_move_num, endgame_move_num=self.endgame_move_num,
                                   time_limit=self.seconds_per_game, decay_factor=self.decay_factor)


# idea borrowed from https://github.com/tensorflow/minigo/blob/master/strategies.py
def time_recommendation(move_num, whole_move_num, endgame_move_num, time_limit, decay_factor):

    move_num /= 2
    whole_move_num /= 2
    endgame_move_num /= 2
    core_move_num = whole_move_num - endgame_move_num

    endgame = (decay_factor - decay_factor ** (endgame_move_num+1)) / (1 - decay_factor)
    base = time_limit / (endgame + core_move_num)

    if move_num < core_move_num:
        return base
    else:
        return (time_limit - base * core_move_num) / endgame * decay_factor ** (move_num - core_move_num)
