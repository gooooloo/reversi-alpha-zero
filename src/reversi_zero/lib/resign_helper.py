import json
import os
from logging import getLogger
from random import random

from src.reversi_zero.lib.chunk_pb2 import ResignFalsePositive, ResignV

logger = getLogger(__name__)


def decide_resign_v_once(config):

    prop = config.play.v_resign_disable_prop
    should_resign = config.play.can_resign and random() >= prop
    if should_resign:
        v, _ = _load_resign(config.resource.resign_log_path)
        v = config.play.v_resign_init if v is None else v
    else:
        v = -99999999

    return ResignV(should_resign=should_resign, v=v)


def handle_resign_false_positive_delta(config, delta):
    assert delta.n >= delta.f_p_n >= 0

    try:
        v, fp = _load_resign(config.resource.resign_log_path)
    except Exception as e:
        logger.debug(e)
        v, fp = None, None

    fp = fp or ResignFalsePositive(n=0, f_p_n=0)
    v = v if v is not None else config.play.v_resign_init

    fp.n += delta.n
    fp.f_p_n += delta.f_p_n
    v = _compute_new_v(config=config, v=v, fp=fp)
    _save_resign(p=config.resource.resign_log_path, v=v, fp=fp)


def _compute_new_v(config, v, fp):
    min_n = config.play.v_resign_check_min_n
    if fp.n < min_n:
        return v

    v_resign_delta = config.play.v_resign_delta
    fraction_t_max = config.play.v_resign_false_positive_fraction_t_max
    fraction_t_min = config.play.v_resign_false_positive_fraction_t_min
    max_v = 1
    min_v = -1

    new_v = v
    n, f_p_n = fp.n, fp.f_p_n

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


def _save_resign(p, v, fp):
    j = dict()
    j['v'] = v
    j['n'] = fp.n
    j['fpn'] = fp.f_p_n
    with open(p, "wt") as f:
        json.dump(j, f)


def _load_resign(fn):
    if os.path.exists(fn):
        with open(fn, "rt") as f:
            j = json.load(f)
            v = j['v']
            c = ResignFalsePositive(n=j['n'], f_p_n=j['fpn'])
            return v, c

    return None, None

