import operator
from logging import getLogger
import requests
import tempfile
import os
import time

logger = getLogger(__name__)


def load_model_weight(model):
    retry_count_max = 10000
    retry_count = 0
    while retry_count < retry_count_max:
        try:
            return load_model_weight_internal(model)
        except Exception as e:
            logger.debug(e)
            logger.debug("will retry")
            # for whatever reason(e.g., network error, fds file synchronization error), we sleep and retry.
            time.sleep(0.1)
            retry_count += 1

    raise Exception(f"Failed to load model after {retry_count_max} tries!")


def load_model_weight_internal(model):
    """

    :param reversi_zero.agent.model.ReversiModel model:
    :return:
    """
    cr = model.config.resource
    if cr.use_remote_model:

        config_file = tempfile.NamedTemporaryFile(delete=False)
        response = requests.get(cr.remote_model_config_path)
        config_file.write(response.content)
        config_file.close()

        weight_file = tempfile.NamedTemporaryFile(delete=False)
        response = requests.get(cr.remote_model_weight_path)
        weight_file.write(response.content)
        weight_file.close()

        logger.debug(f"using remote model from {cr.remote_model_weight_path}")
        loaded = model.load(config_file.name, weight_file.name)

        os.unlink(config_file.name)
        os.unlink(weight_file.name)

        return loaded

    else:
        return model.load(cr.model_config_path, cr.model_weight_path)


def save_model_weight(model, steps):
    """

    :param reversi_zero.agent.model.ReversiModel model:
    :return:
    """
    cr = model.config.resource
    if cr.use_remote_model:
        raise Exception("not supported yet!")  # this should be a upload
    return model.save(model.config.resource.model_config_path, model.config.resource.model_weight_path, steps)


def fetch_model_weight_digest(config):
    """

    :param reversi_zero.agent.model.ReversiModel model:
    :return:
    """
    from reversi_zero.agent.model import ReversiModel
    cr = config.resource
    if cr.use_remote_model:
        config_file = tempfile.NamedTemporaryFile(delete=False)
        response = requests.get(cr.remote_model_weight_path)
        config_file.write(response.content)
        config_file.close()

        digest = ReversiModel.fetch_digest(config_file.name)

        os.unlink(config_file.name)
    else:
        digest = ReversiModel.fetch_digest(cr.model_weight_path)

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


