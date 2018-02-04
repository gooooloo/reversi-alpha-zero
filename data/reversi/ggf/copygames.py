if __name__ == '__main__':
    import glob
    import os
    import re
    import shutil
    from collections import defaultdict, namedtuple

    class Result:
        def __init__(self):
            self.win = self.draw = self.lose = 0

        def __repr__(self):
            return f'{self.win}/{self.draw}/{self.lose}'

    d = defaultdict(lambda : defaultdict(lambda : defaultdict(lambda : Result())))

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

        p = re.compile('.*reversi-NTest_(\d*)-ARZ_(\d*)_(\d*)min-(\d*)_(\d*).*ggf$')
        m = p.match(fn)
        if ntest_lv is None and m:
            ntest_lv = int(m.group(1))
            arz_gen = int(m.group(2))
            arz_sim = None
            arz_min = int(m.group(3))
            ntest_score = int(m.group(4))
            arz_score = int(m.group(5))

        p = re.compile('.*reversi-ARZ_(\d*)_(\d*)-NTest_(\d*)-(\d*)_(\d*).*ggf$')
        m = p.match(fn)
        if ntest_lv is None and m:
            arz_gen = int(m.group(1))
            arz_sim = int(m.group(2))
            arz_min = None
            ntest_lv = int(m.group(3))
            arz_score = int(m.group(4))
            ntest_score = int(m.group(5))

        p = re.compile('.*reversi-ARZ_(\d*)_(\d*)min-NTest_(\d*)-(\d*)_(\d*).*ggf$')
        m = p.match(fn)
        if ntest_lv is None and m:
            arz_gen = int(m.group(1))
            arz_sim = None
            arz_min = int(m.group(2))
            ntest_lv = int(m.group(3))
            arz_score = int(m.group(4))
            ntest_score = int(m.group(5))

        if ntest_lv is None:
            continue

        if arz_score < ntest_score:
            continue

        dest_folder = os.path.join(os.path.dirname(fn), '../../../../reversi-alpha-zero-models/ggf', f'step-{arz_gen}')
        if arz_sim:
            dest_folder = os.path.join(dest_folder, f'sim-{arz_sim}')
        else:
            dest_folder = os.path.join(dest_folder, f'min-{arz_min}')
        dest_folder = os.path.join(dest_folder, f'ntest-{ntest_lv}')
        os.makedirs(dest_folder, exist_ok=True)
        dest = os.path.join(dest_folder, os.path.basename(fn))
        shutil.copy(fn, dest)
