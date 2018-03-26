import operator
from logging import getLogger, INFO
import tempfile
import os
import time

from src.reversi_zero.agent.model import ReversiModel
from src.reversi_zero.lib.grpc_helper import GrpcClient

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


def _load_model_weight_internal(model, grpc_client:GrpcClient):
    config_file = tempfile.NamedTemporaryFile(delete=False)
    config_file.close()
    grpc_client.download_model_config(config_file.name)

    weight_file = tempfile.NamedTemporaryFile(delete=False)
    weight_file.close()
    grpc_client.download_model_weight(weight_file.name)

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

    grpc_client.download_model_config(config_file.name)
    digest = ReversiModel.load_step_info(config_file.name)

    os.unlink(config_file.name)

    return digest


def ask_model_dir(config):
    import os
    dir = config.resource.generation_model_dir
    ng_dict = dict(enumerate(os.listdir(dir)))
    if len(ng_dict) == 0:
        return config.resource.model_dir
    to_print = [f'{x[0]:3}: {x[1]:50}' for x in sorted(ng_dict.items(), key=operator.itemgetter(1))]
    to_print = [''.join(to_print[i:i+2]) for i in range(0, len(to_print), 2)]
    print()
    for job in to_print:
        print(job)
    print()

    max_n = len(ng_dict)
    while True:
        n = input(f'select the model generation 0-{max_n-1}: (click ENTER for best model) ')
        if not n or len(n) == 0:
            return None
        try:
            n = int(n)
        except Error:
            continue
        if 0 <= n < max_n:
            return os.path.join(dir, ng_dict[n])


