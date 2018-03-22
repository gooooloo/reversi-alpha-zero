from glob import glob
from datetime import datetime
from logging import getLogger, WARNING
from random import random
from time import sleep
import tempfile
import requests
import os
import json

from src.reversi_zero.lib.grpc_helper import FileClient

logger = getLogger(__name__)
getLogger('requests.packages.urllib3.connectionpool').setLevel(WARNING)


class ResignCtrl:
    def __init__(self, n=0, f_p_n=0):
        self.n = n
        self.f_p_n = f_p_n

    def __iadd__(self, other):
        self.n += other.n
        self.f_p_n += other.f_p_n
        return self


def compute_resign_v(config):

    prop = config.play.v_resign_disable_prop
    enabled = config.play.can_resign and random() >= prop
    if enabled:
        loaded_v, _ = _load_resign(config.resource.resign_log_path)
        resign_v = config.play.v_resign_init if loaded_v is None else loaded_v
    else:
        resign_v = -99999999

    return enabled, resign_v


def handle_resign_ctrl_delta(config, delta):
    try:
        v, ctrl = _load_resign(config.resource.resign_log_path)
    except Exception as e:
        logger.debug(e)
        v, ctrl = None, None

    ctrl = ctrl or ResignCtrl()
    v = v if v is not None else config.play.v_resign_init

    ctrl += delta
    v = _new_v(config=config, v=v, ctrl=ctrl)
    p = os.path.join(config.resource.resign_log_dir, config.resource.resign_log_path)
    _save_resign(p=p, v=v, ctrl=ctrl)


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

