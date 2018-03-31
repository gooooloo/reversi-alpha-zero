from src.reversi_zero.lib.ggf import GGF


class IEnv:
    @property
    def black_loses(self): raise Exception("not yet implemented")

    @property
    def black_wins(self): raise Exception("not yet implemented")

    @property
    def cob_dtype(self): raise Exception("not yet implemented")

    @property
    def done(self): raise Exception("not yet implemented")

    @property
    def last_player(self): raise Exception("not yet implemented")

    @property
    def last_player_loses(self): raise Exception("not yet implemented")

    @property
    def last_player_wins(self): raise Exception("not yet implemented")

    @property
    def legal_moves(self): raise Exception("not yet implemented")

    @property
    def observation(self): raise Exception("not yet implemented")

    @property
    def rotate_flip_op_count(self): raise Exception("not yet implemented")

    @property
    def score(self): raise Exception("not yet implemented")

    def color_of_vertex(self, r, c): raise Exception("not yet implemented")

    def compress_ob(self, ob): raise Exception("not yet implemented")

    def copy(self): raise Exception("not yet implemented")

    def counter_rotate_flip_pi(self, pi, op): raise Exception("not yet implemented")

    def decompress_ob(self, cob): raise Exception("not yet implemented")

    def equals(self, r): raise Exception("don't call")

    def is_legal(self, action): raise Exception("not yet implemented")

    def render(self): raise Exception("not yet implemented")

    def reset(self): raise Exception("not yet implemented")

    def resign(self): raise Exception("not yet implemented")

    def rotate_flip_ob(self, ob, op): raise Exception("not yet implemented")

    def rotate_flip_pi(self, pi, op): raise Exception("not yet implemented")

    def step(self, action): raise Exception("not yet implemented")

    def new_ggf(self) -> GGF: raise Exception("not yet implemented")

