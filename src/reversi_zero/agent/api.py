import numpy as np
from src.reversi_zero.config import Config
from src.reversi_zero.lib.grpc_helper import FileClient
from src.reversi_zero.lib.pipe_helper import PipePair

BUFFER_DTYPE = np.float32

MODEL_SERVING_READY = 1
MODEL_SERVING_START = 2
MODEL_SERVING_STARTED = 3
MODEL_SERVING_STOP = 4
MODEL_SERVING_STOPPED = 5


class ReversiModelAPISimple:
    def __init__(self, config: Config, agent_model):
        self.config = config
        self.agent_model = agent_model

    def predict(self, x):
        assert x.ndim in (3, 4), f'{x.ndim}'
        assert x.shape == self.config.model.input_size or x.shape[1:] == self.config.model.input_size, f'{x.shape}'
        orig_x = x
        if x.ndim == 3:
            x = x.reshape((1,) + self.config.model.input_size)
        policy, value = self.agent_model.model.predict_on_batch(x)

        if orig_x.ndim == 3:
            return policy[0], value[0]
        else:
            return policy, value


class ReversiModelAPIServer:
    def __init__(self, config: Config, parent_pipe_pair, data_pipe_pairs):
        self.config = config
        self.agent_model = None

        self.parent_pipe_pair = parent_pipe_pair
        self.data_pipe_pairs = data_pipe_pairs
        self.file_client = FileClient(config)

    def start(self):
        self.predict_batch_worker()

    def _load_model(self):
        from src.reversi_zero.agent.model import ReversiModel
        from src.reversi_zero.lib.model_helpler import load_remote_model_weight
        self.agent_model = ReversiModel(self.config)
        steps = load_remote_model_weight(self.agent_model, self.file_client)

        target_steps = self.config.opts.model_serving_step_check
        while target_steps is not None and steps != target_steps:
            print(f'model loading, exp step {target_steps}, act step {steps}')
            self.agent_model = ReversiModel(self.config)
            steps = load_remote_model_weight(self.agent_model, self.file_client)

        if steps is None:
            raise Exception('no model!')

    def predict(self, x):
        assert x.ndim == 4, f'{x.ndim}'
        assert x.shape[1:] == self.config.model.input_size, f'{x.shape}'
        return self.agent_model.model.predict_on_batch(x)

    def predict_batch_worker(self):
        self._load_model()
        for pp in self.data_pipe_pairs:
            pp.open_read_nonblock()

        self.parent_pipe_pair.open_write_nonblock()
        self.parent_pipe_pair.write_int(MODEL_SERVING_READY)
        self.parent_pipe_pair.close_write()

        self.parent_pipe_pair.open_read_nonblock()
        x = self.parent_pipe_pair.read_int(allow_empty=False, sleep_second=0.001)
        assert x == MODEL_SERVING_START

        self.parent_pipe_pair.open_write_nonblock()
        self.parent_pipe_pair.write_int(MODEL_SERVING_STARTED)
        self.parent_pipe_pair.close_write()

        input_len_per_batch = 1
        for x in self.config.model.input_size:
            input_len_per_batch *= x
        input_len_per_batch = int(input_len_per_batch)

        output_len_per_batch = self.config.model.policy_size + 1

        max_batches = 1000
        pool_x = np.empty((max_batches * input_len_per_batch), dtype=BUFFER_DTYPE)
        pool_empty = np.empty((max_batches * input_len_per_batch), dtype=BUFFER_DTYPE)
        pool_y = np.empty((max_batches * output_len_per_batch), dtype=BUFFER_DTYPE)

        while True:
            x = self.parent_pipe_pair.read_int(allow_empty=True)
            if x:
                assert x == MODEL_SERVING_STOP
                self.parent_pipe_pair.close_read()
                self.parent_pipe_pair.open_write_nonblock()
                self.parent_pipe_pair.write_int(MODEL_SERVING_STOPPED)
                self.parent_pipe_pair.close_write()
                break

            batch_begin = 0
            batch_slices = []
            flattern_begin = 0

            pis = []
            for i, pp in enumerate(self.data_pipe_pairs):
                x = pp.read_exact(buffer_size=4, allow_empty=True)
                if x is None or len(x) == 0:
                    continue
                to_read_len = int.from_bytes(x, 'big')
                if to_read_len == 0:
                    continue
                x = pp.read_exact(buffer_size=to_read_len, allow_empty=False)

                x =np.frombuffer(x,dtype=BUFFER_DTYPE)
                assert len(x) % input_len_per_batch == 0, f'{len(x)}, {x}, {input_len_per_batch}'
                batch_end = batch_begin + len(x) // input_len_per_batch
                batch_slices.append(slice(batch_begin, batch_end))
                batch_begin = batch_end

                flattern_end = flattern_begin + len(x)
                np.copyto(pool_x[flattern_begin:flattern_end], x)
                flattern_begin = flattern_end

                pis.append(i)

            if flattern_begin == 0:
                continue

            all_x = pool_x[:flattern_begin].reshape([batch_begin] + list(self.config.model.input_size))

            all_y = self.predict(all_x)
            all_p, all_v = all_y

            np.copyto(pool_x[:flattern_begin], pool_empty[:flattern_begin])

            for s, pi in zip(batch_slices, pis):
                p = all_p[s].ravel()
                np.copyto(pool_y[:len(p)], p)
                v = all_v[s].ravel()
                np.copyto(pool_y[len(p):len(p)+len(v)], v)

                to_write = pool_y[:len(p)+len(v)].data
                byte_length = len(to_write)*pool_y.dtype.itemsize
                self.data_pipe_pairs[pi].open_write_nonblock()
                self.data_pipe_pairs[pi].write(byte_length.to_bytes(4, 'big'))
                self.data_pipe_pairs[pi].write(to_write)
                self.data_pipe_pairs[pi].close_write()

                np.copyto(pool_y[:len(p)+len(v)], pool_empty[:len(p)+len(v)])


class ReversiModelAPIProxy:
    def __init__(self, config, pipe_pair: PipePair):
        self.config = config
        self.pipe_pair = pipe_pair
        self.pipe_pair.open_read_nonblock()

    def predict(self, x):
        assert x.ndim in (3, 4), f'{x.ndim}'
        orig_x_ndim = x.ndim
        batch_number = x.shape[0] if x.ndim == 4 else 1
        if x.ndim == 3:
            x = x.reshape((1,) + self.config.model.input_size)
        assert x.shape[1:] == self.config.model.input_size, f'{x.shape}'

        x = np.asarray(x, dtype=BUFFER_DTYPE)
        x = x.ravel()
        byte_length = len(x)*x.dtype.itemsize
        self.pipe_pair.open_write_nonblock()
        self.pipe_pair.write(byte_length.to_bytes(4, 'big'))
        self.pipe_pair.write(x.data)
        self.pipe_pair.close_write()

        y = self.pipe_pair.read_exact(buffer_size=4, allow_empty=False, sleep_second=0.001)
        to_read_len = int.from_bytes(y, 'big')
        assert to_read_len > 0
        y = self.pipe_pair.read_exact(buffer_size=to_read_len, allow_empty=False, sleep_second=0.001)

        y = np.frombuffer(y, dtype=BUFFER_DTYPE)
        assert len(y) == batch_number * (self.config.model.policy_size + 1), \
            f'get len {len(y)} array, expected len : {batch_number * (self.config.model.policy_size + 1)}'

        p = y[:-batch_number]
        p.shape = [batch_number, self.config.model.policy_size]

        v = y[-batch_number:]
        v.shape = [batch_number]

        if orig_x_ndim == 3:
            p, v = p[0], v[0]

        return p, v
