from datetime import datetime
from glob import glob
from logging import getLogger
import json
import os

from src.reversi_zero.config import ResourceConfig

logger = getLogger(__name__)


def get_game_data_filenames(rc: ResourceConfig):
    pattern = os.path.join(rc.play_data_dir, rc.play_data_filename_tmpl % "*")
    files = list(sorted(glob(pattern)))
    return files


def get_game_data_statistics_filename(rc: ResourceConfig):
    return os.path.join(rc.play_data_dir, rc.play_data_statistics_filename)


def read_game_data_from_file(path):
    with open(path, "rt") as f:
        return json.load(f)


def save_play_data(rc, moves):
    game_id = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
    path = os.path.join(rc.play_data_dir, rc.play_data_filename_tmpl % game_id)
    logger.info(f"save play data to {path}")
    with open(path, "wt") as f:
        json.dump(moves, f)


def remove_old_play_data(config):
    files = get_game_data_filenames(config.resource)
    if len(files) < config.play_data.max_file_num:
        return
    for i in range(len(files) - config.play_data.max_file_num):
        try:
            os.remove(files[i])
        except FileNotFoundError:
            # Fine. Maybe due to multiple processes parallelsim.
            logger.debug(f'fail to remove file {files[i]}')


KEY_UNLOADED_DATA_COUNT = 'unloaded_data_count'


def save_unloaded_data_count(rc: ResourceConfig, count):
    fn = get_game_data_statistics_filename(rc)
    with open(fn, "wt") as f:
        json.dump({KEY_UNLOADED_DATA_COUNT: count}, f)


def load_unloaded_data_count(rc: ResourceConfig):
    fn = get_game_data_statistics_filename(rc)
    try:
        with open(fn, "rt") as f:
            d = json.load(f)
        if d and KEY_UNLOADED_DATA_COUNT in d:
            return int(d[KEY_UNLOADED_DATA_COUNT])
        else:
            return 0
    except Exception as e:
        logger.info(e)
        return 0
