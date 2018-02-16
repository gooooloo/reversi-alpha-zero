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
        self.pipe_names = []
        self.pipe_idx = 0

    def make_pipes(self, n_pipes):
        os.makedirs(self.pipe_folder, exist_ok=True)

        n = self.pipe_idx
        pns = [self.get_pipe_name(n+i) for i in range(2*n_pipes)]
        self.pipe_idx += len(pns)
        self.pipe_names.extend(pns)

        for pn in pns:
            os.mkfifo(pn)

        return [PipePair(pns[2*i], pns[2*i+1]) for i in range(n_pipes)]

    def get_pipe_name(self, i):
        return f'{self.pipe_folder}/pp_{i}_{time.time()}_{random.randint(100000, 999999)}'

    def clear_pipes(self):

        if self.pipe_names:
            for pn in self.pipe_names:
                os.unlink(pn)

        self.pipe_names = []

    def clear_a_pipe(self, pp):
        if pp:
            assert pp.pipe_in is None, 'close it first'
            assert pp.pipe_out is None, 'close it first'

            for n in (pp.in_name, pp.out_name):
                assert n in self.pipe_names
                self.pipe_names.remove(n)
                os.unlink(n)

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
        self.pipe_out = None

    def reverse_in_out(self):
        return PipePair(self.out_name, self.in_name)

    def dump_names(self):
        j = self.__dict__.copy()
        j.pop('pipe_in')
        j.pop('pipe_out')
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

    def open_write_nonblock(self):
        assert self.pipe_out is None, 'do not open twice'
        myprint(f'start open nonblock write {self.out_name}')
        self.pipe_out = os.open(self.out_name, os.O_WRONLY | os.O_NONBLOCK)
        myprint(f'done open nonblock write {self.out_name}')

    def open_write_block(self):
        assert self.pipe_out is None, 'do not open twice'
        myprint(f'start open block write {self.out_name}')
        self.pipe_out = os.open(self.out_name, os.O_WRONLY)
        myprint(f'done open block write {self.out_name}')

    def close_write(self):
        assert self.pipe_out, 'have you called open_write_*()?'
        os.close(self.pipe_out)
        self.pipe_out = None

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
        assert self.pipe_out, 'have you called open_write_nonblock()?'
        os.write(self.pipe_out, data)

    def write_int(self, i):
        self.write(int(i).to_bytes(4, 'big'))

    def read_int(self, allow_empty, sleep_second=None):
        b = self.read_exact(buffer_size=4, allow_empty=allow_empty, sleep_second=sleep_second)
        return int.from_bytes(b, 'big') if b else None

    def write_bytes(self, b, length=None):
        assert b is not None
        length = length or len(b)
        self.write_int(length)
        self.write(b)

    def read_bytes(self, allow_empty):
        length = self.read_int(allow_empty)
        if length:
            return self.read_exact(length, allow_empty=False)
        else:
            return None


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
