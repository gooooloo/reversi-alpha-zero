import errno
import json
import os
import random
import signal

import sys

import time


def myprint(*args):
    if False:
        print(*args)

class PipeFilesManager:

    @staticmethod
    def new_one(config):
        pfm = PipeFilesManager(f'/tmp/reresi_alpha_zero/{config.env.env_class_name}')
        pfm.signal_exit()
        return pfm

    def __init__(self, pipe_folder):
        self.agent_model = None

        self.pipe_folder = pipe_folder
        self.pipe_names_in = None
        self.pipe_names_out = None

    def make_pipes(self, n_pipes):
        os.makedirs(self.pipe_folder, exist_ok=True)

        self.pipe_names_in = [self.get_pipe_name_in(i) for i in range(n_pipes)]
        self.pipe_names_out = [self.get_pipe_name_out(i) for i in range(n_pipes)]

        for pin in self.pipe_names_in:
            os.mkfifo(pin)
        for pout in self.pipe_names_out:
            os.mkfifo(pout)

        return [PipePair(x, y) for x,y in zip(self.pipe_names_in, self.pipe_names_out)]

    def get_pipe_name_in(self, i):
        return f'{self.pipe_folder}/in_{i}_{time.time()}_{random.randint(100000, 999999)}'

    def get_pipe_name_out(self, i):
        return f'{self.pipe_folder}/out_{i}_{time.time()}_{random.randint(100000, 999999)}'

    def clear_pipes(self):

        if self.pipe_names_in:
            for pin in self.pipe_names_in:
                os.unlink(pin)

        if self.pipe_names_out:
            for pout in self.pipe_names_out:
                os.unlink(pout)

        self.pipe_names_in = None
        self.pipe_names_out = None

    def signal_exit(self):
        def clean(*args):
            self.clear_pipes()

        from src.reversi_zero.lib.proc_helper import add_exit_task
        add_exit_task(clean)


class PipePair:
    def __init__(self, in_name, out_name):
        self.in_name = in_name
        self.out_name = out_name

        self.pipe_in = None

    def reverse_in_out(self):
        return PipePair(self.out_name, self.in_name)

    def dump_names(self):
        j = self.__dict__.copy()
        j.pop('pipe_in')
        return json.dumps(j)

    @staticmethod
    def load_names(s):
        return PipePair(**json.loads(s))

    def open_read_nonblock(self):
        assert self.pipe_in is None, 'do not open twice'
        myprint(f'start open nonblock read {self.in_name}')
        self.pipe_in = os.open(self.in_name, os.O_RDONLY | os.O_NONBLOCK)
        myprint(f'done open nonblock read {self.in_name}')

    def close_read(self):
        assert self.pipe_in, 'have you called open_read_nonblock()?'
        os.close(self.pipe_in)
        self.pipe_in = None

    def try_read_allow_empty(self, max_buffer_size=99999):
        assert self.pipe_in, 'have you called open_read_nonblock()?'

        try:
            return os.read(self.pipe_in, max_buffer_size)
        except OSError as err:
            if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
                return None
            else:
                raise

    def read_no_empty(self, max_buffer_size=99999, sleep_retry=None):
        y = self.try_read_allow_empty(max_buffer_size)
        while y is None or len(y) == 0:
            if sleep_retry:
                time.sleep(sleep_retry)
            y = self.try_read_allow_empty(max_buffer_size)
        return y

    def read_exact(self, buffer_size, allow_empty, sleep_second=None):
        assert self.pipe_in, 'have you called open_read_nonblock()?'

        all_x = bytes()
        while True:
            try:
                x = os.read(self.pipe_in, buffer_size-len(all_x))
                if allow_empty:
                    all_x = x
                    break
                elif x and len(x) == buffer_size:
                    all_x = x
                    break
                elif x and len(x) > 0:
                    all_x = b''.join([all_x, x])
                else:
                    pass

                if sleep_second:
                    time.sleep(sleep_second)

            except OSError as err:
                if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
                    if sleep_second:
                        time.sleep(sleep_second)
                else:
                    raise
        return all_x

    def read_once(self, max_buffer_size=99999):
        myprint(f'start open read {self.in_name}')
        pipe_in = os.open(self.in_name, os.O_RDONLY)
        myprint(f'done open read {self.in_name}')
        y = os.read(pipe_in, max_buffer_size)  # may block here
        os.close(pipe_in)
        return y

    def write(self, data):
        myprint(f'start open write {self.out_name}')
        f = os.open(self.out_name, os.O_WRONLY)
        myprint(f'done open write {self.out_name}')
        os.write(f, data)
        os.close(f)

    def write_nonblock(self, data):
        myprint(f'start open nonblock write {self.out_name}')
        f = os.open(self.out_name, os.O_WRONLY | os.O_NONBLOCK)
        myprint(f'done open nonblock write {self.out_name}')
        os.write(f, data)
        os.close(f)

def reverse_in_out(pairs):
    list = []
    for pp in pairs:
        list.append(pp.reverse_in_out())
    return list

def dump_pipe_pairs_names(pairs):
    assert len(pairs) > 0
    assert isinstance(pairs[0], PipePair)

    return json.dumps([pp.dump_names() for pp in pairs])


def load_pipe_pairs_names(s):
    ll = json.loads(s)
    return [PipePair.load_names(x) for x in ll]


if __name__ == '__main__':
    pp = PipePair('/a/a', '/b/b')
    myprint(pp.dump_names())
    myprint(PipePair.load_names(pp.dump_names()))

    pp1 = PipePair('/a/a', '/b/b')
    pp2 = PipePair('/c/c', '/d/d')
    pp3 = PipePair('/e/e', '/f/f')
    pplist = [pp1, pp2, pp3]
    myprint(dump_pipe_pairs_names(pplist))
    myprint(load_pipe_pairs_names(dump_pipe_pairs_names(pplist)))

    myprint(len(pplist))
    for pp in pplist:
        myprint(pp)
