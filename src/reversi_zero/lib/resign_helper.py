from glob import glob
from datetime import datetime
from logging import getLogger
from time import sleep
import tempfile
import requests
import os
import json

logger = getLogger(__name__)


class ResignCtrl:
    def __init__(self, n=0, f_p_n=0):
        self.n = n
        self.f_p_n = f_p_n

    def __iadd__(self, other):
        self.n += other.n
        self.f_p_n += other.f_p_n
        return self


def load_resign_v(config):
    if config.resource.use_remote_model:
        v, _ = _load_resign_remote(config)
    else:
        v, _ = _load_resign_local(config)

    return v


def _load_resign_local(config):
    try:
        p = config.resource.resign_log_path
        return _load_resign(p)
    except Exception as e:
        logger.debug(e)

    return None, None


def _load_resign_remote(config):
    p = None
    try:
        p = tempfile.NamedTemporaryFile(delete=False)
        response = requests.get(config.resource.remote_resign_log_path)
        p.write(response.content)
        p.close()
        return _load_resign(p.name)

    except Exception as e:
        logger.debug(e)
    finally:
        if p:
            os.unlink(p.name)

    return None, None


# just save in file as a report, another process would handle it
def report_resign_ctrl(config, ctrl):
    t = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
    p = os.path.join(config.resource.resign_log_dir, config.resource.resign_delta_path_tmpl % t)
    _save_resign(v=None, ctrl=ctrl, p=p)


def keep_updating_resign_ctrl(config):
    v, ctrl = _load_resign_local(config)
    ctrl = ctrl or ResignCtrl()
    v = v if v is not None else config.play.v_resign_init

    while True:
        fns = _get_resign_delta_filenames(config)
        for fn in fns:
            try:
                _, delta = _load_resign(fn)
            except Exception as e:
                logger.debug(e)
                dalta = None

            if not delta:
                continue
            ctrl += delta
            v = _new_v(config=config, v=v, ctrl=ctrl)
            p = os.path.join(config.resource.resign_log_dir, config.resource.resign_log_path)
            _save_resign(p=p, v=v, ctrl=ctrl)
            os.remove(fn)

        sleep_seconds = 10
        logger.info(f'resign_v updated to {v}. sleeping {sleep_seconds} seconds...')
        sleep(sleep_seconds)


def _get_resign_delta_filenames(config):
    pattern = os.path.join(config.resource.resign_log_dir, config.resource.resign_delta_path_tmpl % "*")
    files = list(sorted(glob(pattern)))
    return files


def _new_v(config, v, ctrl):
    min_n = config.play.v_resign_check_min_n
    if ctrl.n < min_n:
        return v

    v_resign_delta = config.play.v_resign_delta
    fraction_t_max = config.play.v_resign_false_positive_fraction_t_max
    fraction_t_min = config.play.v_resign_false_positive_fraction_t_min
    max_v = 0.95
    min_v = -0.95

    new_v = v
    n, f_p_n = ctrl.n, ctrl.f_p_n

    fraction = float(f_p_n) / n
    logger.debug(f'resign f_p frac: {f_p_n} / {n} = {fraction}')
    if fraction > fraction_t_max:
        new_v -= v_resign_delta
    elif fraction < fraction_t_min:
        new_v += v_resign_delta
    else:
        pass

    new_v = max(min_v, new_v)
    new_v = min(max_v, new_v)

    if abs(new_v - v) > 1e-10:
        logger.debug(f'#false_positive={f_p_n}, #n={n}, frac={fraction}, target_fract=[{fraction_t_min},{fraction_t_max}]')
        logger.debug(f'v_resign change from {v} to {new_v}')

    return new_v


def _save_resign(p, v, ctrl):
    j = dict()
    j['v'] = v
    j['n'] = ctrl.n
    j['fpn'] = ctrl.f_p_n
    with open(p, "wt") as f:
        json.dump(j, f)


def _load_resign(fn):
    if os.path.exists(fn):
        with open(fn, "rt") as f:
            j = json.load(f)
            v = j['v']
            c = ResignCtrl(n=j['n'], f_p_n=j['fpn'])
            return v, c

    return None, None

