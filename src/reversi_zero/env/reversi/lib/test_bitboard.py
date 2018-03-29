from nose.tools.trivial import ok_, eq_

from reversi_zero.lib.bitboard import find_correct_moves, board_to_string
from reversi_zero.lib.util import parse_to_bitboards

def parse_to_bitboards(string: str):
    lines = string.strip().split("\n")
    black = 0
    white = 0
    y = 0

    for line in [l.strip() for l in lines]:
        if line[:2] == '##':
            continue
        for i, ch in enumerate(line[1:9]):
            if ch == 'O':
                black |= 1 << (y*8+i)
            elif ch == 'X':
                white |= 1 << (y*8+i)
        y += 1

    return black, white


def test_parse_to_bitboards_init():
    ex = '''
    ##########
    #        #
    #        #
    #        #
    #   OX   #
    #   XO   #
    #        #
    #        #
    #        #
    ##########
    '''

    black, white = util.parse_to_bitboards(ex)
    eq_(black, 0b00001000 << 24 | 0b00010000 << 32, f"{ex}\n-------\n{board_to_string(black, white)}")
    eq_(white, 0b00010000 << 24 | 0b00001000 << 32, f"{ex}\n-------\n{board_to_string(black, white)}")


def test_parse_to_bitboards():
    ex = '''
##########
#OO      #
#XOO     #
#OXOOO   #
#  XOX   #
#   XXX  #
#  X     #
# X      #
#       X#
##########'''

    black, white = util.parse_to_bitboards(ex)
    eq_(ex.strip(), board_to_string(black, white).strip(), f"{ex}\n-------\n{board_to_string(black, white)}")

def test_find_correct_moves_1():
    ex = '''
##########
#OO      #
#XOO     #
#OXOOO   #
#  XOX   #
#   XXX  #
#  X     #
# X      #
#        #
##########'''

    expect = '''
##########
#OO      #
#XOO     #
#OXOOO   #
#**XOX*  #
# **XXX  #
#  X**** #
# X      #
#        #
##########
'''
    _flip_test(ex, expect)


def _flip_test(ex, expect, player_black=True):
    b, w = parse_to_bitboards(ex)
    moves = find_correct_moves(b, w) if player_black else find_correct_moves(w, b)
    res = board_to_string(b, w, extra=moves)
    eq_(res.strip(), expect.strip(), f"\n{res}----{expect}")


def test_find_correct_moves_2():
    ex = '''
##########
#OOOOOXO #
#OOOOOXOO#
#OOOOOXOO#
#OXOXOXOO#
#OOXOXOXO#
#OOOOOOOO#
#XXXO   O#
#        #
##########'''

    expect = '''
##########
#OOOOOXO*#
#OOOOOXOO#
#OOOOOXOO#
#OXOXOXOO#
#OOXOXOXO#
#OOOOOOOO#
#XXXO***O#
#   *    #
##########'''

    _flip_test(ex, expect, player_black=False)


def test_find_correct_moves_3():
    ex = '''
##########
#OOXXXXX #
#XOXXXXXX#
#XXXXXXXX#
#XOOXXXXX#
#OXXXOOOX#
#OXXOOOOX#
#OXXXOOOX#
# OOOOOOO#
##########'''

    expect1 = '''
##########
#OOXXXXX #
#XOXXXXXX#
#XXXXXXXX#
#XOOXXXXX#
#OXXXOOOX#
#OXXOOOOX#
#OXXXOOOX#
#*OOOOOOO#
##########'''

    expect2 = '''
##########
#OOXXXXX*#
#XOXXXXXX#
#XXXXXXXX#
#XOOXXXXX#
#OXXXOOOX#
#OXXOOOOX#
#OXXXOOOX#
# OOOOOOO#
##########'''

    _flip_test(ex, expect1, player_black=False)
    _flip_test(ex, expect2, player_black=True)



