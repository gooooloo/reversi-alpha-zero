import importlib
import os
from bisect import bisect
from logging import getLogger
from random import randint
from time import sleep

import keras.backend as K
import numpy as np
from keras.optimizers import SGD

from src.reversi_zero.agent.model import ReversiModel, objective_function_for_policy, objective_function_for_value
from src.reversi_zero.config import Config
from src.reversi_zero.lib import tf_util
from src.reversi_zero.lib.data_helper import get_game_data_filenames, read_game_data_from_file, \
    save_unloaded_data_count, load_unloaded_data_count
from src.reversi_zero.lib.model_helpler import load_model_weight, save_model_weight

logger = getLogger(__name__)
logger.setLevel(INFO)


def start(config: Config):
    if config.opts.gpu_mem_frac is not None:
        tf_util.set_session_config(per_process_gpu_memory_fraction=config.opts.gpu_mem_frac)
    return OptimizeWorker(config).start()


class DataSet:
    def __init__(self, loaded_data):
        self.length_array = []
        self.filename_array = []

        total_length = 0
        for filename in loaded_data:
            length = len(loaded_data[filename])
            total_length += length

            self.length_array.append(total_length)
            self.filename_array.append(filename)

    def locate(self, index):
        p = bisect(self.length_array, index)
        offset = index - self.length_array[p-1] if p > 0 else index
        return self.filename_array[p], offset

    @property
    def size(self):
        return self.length_array[-1]


class OptimizeWorker:
    def __init__(self, config: Config):
        self.config = config
        self.model = None  # type: ReversiModel
        self.total_steps = 0
        self.loaded_filenames = set()
        self.loaded_data = {}
        self.dataset = None
        self.optimizer = None
        self.unloaded_data_count = 0

    def start(self):
        self.model, self.total_steps = self.load_model()

        # overwrite if caller requires to
        if self.config.trainer.start_total_steps > 0:
            self.total_steps = self.config.trainer.start_total_steps

        self.unloaded_data_count = load_unloaded_data_count(self.config.resource)

        self.training()

    def training(self):
        self.compile_model()
        last_generation_step = last_save_step = 0
        min_data_size_to_learn = self.config.trainer.min_data_size_to_learn
        self.load_play_data()

        while True:
            if self.dataset_size < min_data_size_to_learn:
                logger.info(f"dataset_size={self.dataset_size} is less than {min_data_size_to_learn}")
                sleep(60)
                self.load_play_data()
                continue
            self.update_learning_rate()
            steps = self.train_epoch(self.config.trainer.epoch_to_checkpoint)
            self.total_steps += steps

            if not self.config.trainer.need_eval:
                if last_generation_step + self.config.trainer.generation_model_steps <= self.total_steps:
                    self.save_current_model_as_generation()
                    last_generation_step = self.total_steps

            if last_save_step + self.config.trainer.save_model_steps <= self.total_steps:
                if self.config.trainer.need_eval:
                    self.save_current_model_as_to_eval()
                else:
                    self.save_current_model()

                last_save_step = self.total_steps

            self.load_play_data()

    def generate_train_data(self, batch_size):
        class_attr = getattr(importlib.import_module(self.config.env.env_module_name), self.config.env.env_class_name)
        env = class_attr()
        # The AZ paper doesn't leverage the symmetric observation data augmentation. But it is nice to use it if we can.
        symmetric_n = env.rotate_flip_op_count

        while True:
            orig_data_size = self.dataset.size
            data_size = orig_data_size * symmetric_n if symmetric_n > 1 else orig_data_size

            x, y1, y2 = [], [], []
            for _ in range(batch_size):
                n = randint(0, data_size - 1)
                orig_n = n // symmetric_n if symmetric_n > 1 else n

                file_name, offset = self.dataset.locate(orig_n)

                state, policy, z = self.loaded_data[file_name][offset]
                state = env.decompress_ob(state)

                if symmetric_n > 1:
                    op = n % symmetric_n
                    state = env.rotate_flip_ob(state, op)
                    policy = env.rotate_flip_pi(policy, op)

                x.append(state)
                y1.append(policy)
                y2.append([z])

            x = np.asarray(x)
            y = [np.asarray(y1), np.asarray(y2)]
            yield x, y

    def train_epoch(self, epochs):
        tc = self.config.trainer
        self.model.model.fit_generator(generator=self.generate_train_data(tc.batch_size),
                                       steps_per_epoch=tc.epoch_steps,
                                       epochs=epochs)
        return tc.epoch_steps * epochs

    def compile_model(self):
        self.optimizer = SGD(lr=1e-2, momentum=0.9)
        losses = [objective_function_for_policy, objective_function_for_value]
        self.model.model.compile(optimizer=self.optimizer, loss=losses)

    def update_learning_rate(self):

        for this_lr, till_step in self.config.trainer.lr_schedule:
            if self.total_steps < till_step:
                lr = this_lr
                break
        K.set_value(self.optimizer.lr, lr)
        logger.info(f"total step={self.total_steps}, set learning rate to {lr}")

    def save_current_model(self):
        save_model_weight(self.model, self.total_steps)

    def save_current_model_as_to_eval(self):
        rc = self.config.resource
        model_dir = os.path.join(rc.to_eval_model_dir, rc.to_eval_model_dirname_tmpl % self.total_steps)
        os.makedirs(model_dir, exist_ok=True)
        config_path = os.path.join(model_dir, rc.model_config_filename)
        weight_path = os.path.join(model_dir, rc.model_weight_filename)
        self.model.save(config_path, weight_path, self.total_steps)

    def save_current_model_as_generation(self):
        rc = self.config.resource
        model_dir = os.path.join(rc.generation_model_dir, rc.generation_model_dirname_tmpl % self.total_steps)
        os.makedirs(model_dir, exist_ok=True)
        config_path = os.path.join(model_dir, rc.model_config_filename)
        weight_path = os.path.join(model_dir, rc.model_weight_filename)
        self.model.save(config_path, weight_path, self.total_steps)

    @property
    def dataset_size(self):
        if self.dataset is None:
            return 0
        return self.dataset.size

    def load_model(self):
        from reversi_zero.agent.model import ReversiModel
        model = ReversiModel(self.config)

        logger.info(f"loading model")
        steps = load_model_weight(model)
        if steps is None:
            raise RuntimeError(f"Model can not loaded!")
        return model, steps

    def load_play_data(self):
        filenames = get_game_data_filenames(self.config.resource)
        updated = False
        for filename in filenames:
            if filename in self.loaded_filenames:
                continue
            self.load_data_from_file(filename)
            updated = True

        for filename in (self.loaded_filenames - set(filenames)):
            self.unload_data_of_file(filename)
            updated = True

        if updated:
            logger.info("updating training dataset")
            self.dataset = DataSet(self.loaded_data)

        logger.info(f'loaded data size: {self.dataset_size}; unloaded data size: {self.unloaded_data_count}')

    def load_data_from_file(self, filename):
        try:
            logger.debug(f"loading data from {filename}")
            data = read_game_data_from_file(filename)
            self.loaded_data[filename] = data
            self.loaded_filenames.add(filename)
        except Exception as e:
            logger.warning(str(e))

    def unload_data_of_file(self, filename):
        logger.debug(f"removing data about {filename} from training set")
        self.loaded_filenames.remove(filename)
        if filename in self.loaded_data:
            self.unloaded_data_count += len(self.loaded_data[filename])
            save_unloaded_data_count(self.config.resource, self.unloaded_data_count)
            del self.loaded_data[filename]
