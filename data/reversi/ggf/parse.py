if __name__ == '__main__':
    import glob
    import re
    from collections import defaultdict, namedtuple

    class Result:
        def __init__(self):
            self.win = self.draw = self.lose = 0

        def __repr__(self):
            return f'{self.win}/{self.draw}/{self.lose}'

    d = defaultdict(lambda : defaultdict(lambda : defaultdict(lambda : defaultdict(lambda: Result()))))

    ntest_lv_set = set()
    arz_gen_set  = set()
    arz_sim_set  = set()

    for fn in glob.glob('**/*', recursive=True):
        p = re.compile('.*reversi-NTest_(\d*)-ARZ_(\d*)_(\d*)-(\d*)_(\d*).*ggf$')
        m = p.match(fn)
        ntest_lv = None
        if m:
            ntest_lv = int(m.group(1))
            arz_gen = int(m.group(2))
            arz_sim = int(m.group(3))
            arz_min = None
            ntest_score = int(m.group(4))
            arz_score = int(m.group(5))
            arz_black = False

        p = re.compile('.*reversi-NTest_(\d*)-ARZ_(\d*)_(\d*)min-(\d*)_(\d*).*ggf$')
        m = p.match(fn)
        if ntest_lv is None and m:
            ntest_lv = int(m.group(1))
            arz_gen = int(m.group(2))
            arz_sim = None
            arz_min = int(m.group(3))
            ntest_score = int(m.group(4))
            arz_score = int(m.group(5))
            arz_black = False

        p = re.compile('.*reversi-ARZ_(\d*)_(\d*)-NTest_(\d*)-(\d*)_(\d*).*ggf$')
        m = p.match(fn)
        if ntest_lv is None and m:
            arz_gen = int(m.group(1))
            arz_sim = int(m.group(2))
            arz_min = None
            ntest_lv = int(m.group(3))
            arz_score = int(m.group(4))
            ntest_score = int(m.group(5))
            arz_black = True

        p = re.compile('.*reversi-ARZ_(\d*)_(\d*)min-NTest_(\d*)-(\d*)_(\d*).*ggf$')
        m = p.match(fn)
        if ntest_lv is None and m:
            arz_gen = int(m.group(1))
            arz_sim = None
            arz_min = int(m.group(2))
            ntest_lv = int(m.group(3))
            arz_score = int(m.group(4))
            ntest_score = int(m.group(5))
            arz_black = True

        if ntest_lv is None:
            continue

        assert arz_sim or arz_min
        assert arz_sim is None or arz_min is None

        arz_sim_min = f'{arz_sim} sim' if arz_sim else f'{arz_min} min'
        if arz_score > ntest_score:
            d[arz_gen][arz_sim_min][ntest_lv][arz_black].win += 1
        if arz_score == ntest_score:
            d[arz_gen][arz_sim_min][ntest_lv][arz_black].draw += 1
        if arz_score < ntest_score:
            d[arz_gen][arz_sim_min][ntest_lv][arz_black].lose += 1

    gen_set = set(x for x in d)
    #gen_set = [x for x in gen_set if x == 513800]
    sim_min_set = set(y for x in d for y in d[x] )
    ntest_lv_set = set(z for x in d for y in d[x] for z in d[x][y])
    ntest_lv_set1 = [x for x in ntest_lv_set if  5 <= x < 8]
    ntest_lv_set2= [x for x in ntest_lv_set if 8 <= x < 11]
    ntest_lv_set3= [x for x in ntest_lv_set if 11 <= x < 14]
    ntest_lv_set4= [x for x in ntest_lv_set if 14 <= x]

    for ntest_lv_set in (ntest_lv_set1, ntest_lv_set2, ntest_lv_set3, ntest_lv_set4):
        s = ''
        s += '|           |         |'
        for ntest_lv in sorted(list(ntest_lv_set)):
            s += f'  Ntest:{ntest_lv:2} |'
            s += f'  Ntest:{ntest_lv:2} |'
        s += '\n'
        s += '|-----------|--------:|'
        for _ in sorted(list(ntest_lv_set)):
            s += ':---------:|'
            s += ':---------:|'
        s += '\n'

        for gen in sorted(list(gen_set)):
            for sim_min in sorted(list(sim_min_set)):
                if sim_min not in d[gen]:
                    continue

                s += f'|step-{gen:6}|'
                s += f'           {sim_min}|'[-10:]
                for ntest_lv in sorted(list(ntest_lv_set)):
                    for side in (True, False):
                        e = d[gen][sim_min][ntest_lv][side]
                        if e.win == 0 and e.draw == 0 and e.lose == 0:
                            s += '     -     |'
                        elif e.win == 0 and e.draw == 0:
                            s += '           |'
                        elif e.win >= e.lose:
                            if e.win > 9:
                                s += f'              {"B" if side else "W"} **{e.win}/{e.draw}/{e.lose}**|'[-13:]
                            else:
                                s += f'              {"B" if side else "W"} **{e.win}/{e.draw}/{e.lose}**|'[-12:]
                        else:
                            s += f'                    {"B" if side else "W"} {e.win}/{e.draw}/{e.lose}  |'[-12:]
                s += '\n'

        print(s)
