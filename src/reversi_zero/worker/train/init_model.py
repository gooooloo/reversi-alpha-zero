import os
from logging import getLogger

from src.reversi_zero.agent.model import ReversiModel
from src.reversi_zero.config import Config

logger = getLogger(__name__)


def start(config: Config):
    model = ReversiModel(config)
    cr = config.resource
    if not os.path.exists(cr.model_config_path) or not os.path.exists(cr.model_weight_path):
        model.build()
        model.save(cr.model_config_path, cr.model_weight_path, 0)
