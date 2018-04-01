from logging import getLogger, INFO
import tempfile
import os
import time

from src.reversi_zero.agent.model import ReversiModel
from src.reversi_zero.lib.chunk_pb2 import ModelStep
from src.reversi_zero.lib.grpc_helper import GrpcClient, simplestring_to_modelstep, MODEL_STEP_TYPE_NEWEST

logger = getLogger(__name__)
logger.setLevel(INFO)


# will never return None
def load_remote_model_weight(model, grpc_client:GrpcClient):
    retry_count_max = 10000
    retry_count = 0
    while retry_count < retry_count_max:
        try:
            ret = _load_model_weight_internal(model, grpc_client)
            if ret is not None:
                return ret
        except Exception as e:
            logger.info(e)
            logger.info("will retry")
        # for whatever reason(e.g., network error), we sleep and retry.
        time.sleep(0.1)
        retry_count += 1

    raise Exception(f"Failed to load model after {retry_count_max} tries!")


def _load_model_weight_internal(model:ReversiModel, grpc_client:GrpcClient):
    model_step = model.config.model.model_step
    if model_step:
        model_step = simplestring_to_modelstep(model_step)
    else:
        model_step = ModelStep(type=MODEL_STEP_TYPE_NEWEST, step=0)

    config_file = tempfile.NamedTemporaryFile(delete=False)
    config_file.close()
    grpc_client.download_model_config_now(config_file.name, model_step)

    weight_file = tempfile.NamedTemporaryFile(delete=False)
    weight_file.close()
    grpc_client.download_model_weight_now(weight_file.name, model_step)

    loaded = model.load(config_file.name, weight_file.name)

    os.unlink(config_file.name)
    os.unlink(weight_file.name)

    return loaded


def fetch_remote_model_step_info_not_none(grpc_client:GrpcClient):
    retry_count_max = 10000
    retry_count = 0
    while retry_count < retry_count_max:
        try:
            ret = _fetch_remote_model_step_info_internal(grpc_client)
            if ret is not None:
                return ret
        except Exception as e:
            logger.info(e)
            logger.info("will retry")
        # for whatever reason(e.g., network error), we sleep and retry.
        time.sleep(0.1)
        retry_count += 1

    raise Exception(f"Failed to load model after {retry_count_max} tries!")


def _fetch_remote_model_step_info_internal(grpc_client:GrpcClient):

    config_file = tempfile.NamedTemporaryFile(delete=False)
    config_file.close()

    model_step = ModelStep(type=MODEL_STEP_TYPE_NEWEST, step=0)
    grpc_client.download_model_config(config_file.name, model_step)
    digest = ReversiModel.load_step_info(config_file.name)

    os.unlink(config_file.name)

    return digest
