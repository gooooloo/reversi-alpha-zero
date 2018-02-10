
from logging import getLogger

import numpy as np

from src.reversi_zero.lib.pipe_helper import PipePair

logger = getLogger(__name__)


class ModelCachePipeHelper:
    def __init__(self):
        self.TYPE_CACHE_QUERY = 1
        self.TYPE_CACHE_CANDIDATE = 2
        self.RESULT_CACHE_HIT = 3
        self.RESULT_CACHE_NOT_FOUND = 4

    def read_type(self, pp):
        t = pp.read_int(allow_empty=True)
        return t if t in (self.TYPE_CACHE_QUERY, self.TYPE_CACHE_CANDIDATE) else None

    def write_cache_query(self, pp, ob: bytes, oblen):
        pp.write_int(self.TYPE_CACHE_QUERY)
        pp.write_bytes(ob, oblen)

    def read_cache_query(self, pp):
        return pp.read_bytes(allow_empty=False)

    def write_cache_query_result(self, pp, p, v):
        if p is not None and v is not None:
            pp.write_int(self.RESULT_CACHE_HIT)
            pp.write_bytes(p)
            pp.write_bytes(v)
        else:
            pp.write_int(self.RESULT_CACHE_NOT_FOUND)

    def read_cache_query_result(self, pp):
        i = pp.read_int(allow_empty=False)
        if i == self.RESULT_CACHE_HIT:
            p = pp.read_bytes(allow_empty=False)
            v = pp.read_bytes(allow_empty=False)
            return p,v
        elif i == self.RESULT_CACHE_NOT_FOUND:
            return None
        else:
            raise Exception('wrong')

    def write_cache_candidate(self, pp, ob, oblen, p, plen, v, vlen):
        pp.write_int(self.TYPE_CACHE_CANDIDATE)
        pp.write_bytes(ob, oblen)
        pp.write_bytes(p, plen)
        pp.write_bytes(v, vlen)

    def read_cache_candidate(self, pp):
        ob = pp.read_bytes(allow_empty=False)
        p = pp.read_bytes(allow_empty=False)
        v = pp.read_bytes(allow_empty=False)
        return ob,(p,v)


class ModelCacheServer:
    def __init__(self, pipe_pairs, model_cache_max_length):
        self.model_cache = dict()
        self.pipe_pairs = pipe_pairs

        self.cache_helper = ModelCachePipeHelper()
        self.model_cache_max_length = model_cache_max_length

    def get_ready(self):
        for pp in self.pipe_pairs:
            pp.open_read_nonblock()

    def serve(self):
        push_count = 0
        while True:
            for pp in self.pipe_pairs:
                t = self.cache_helper.read_type(pp)

                if t == self.cache_helper.TYPE_CACHE_QUERY:
                    ob = self.cache_helper.read_cache_query(pp)

                    if ob:
                        p,v = self.model_cache[ob] if ob in self.model_cache else (None, None)

                        pp.open_write_nonblock()
                        self.cache_helper.write_cache_query_result(pp, p, v)
                        pp.close_write()

                elif t == self.cache_helper.TYPE_CACHE_CANDIDATE:
                    ob,(p,v) = self.cache_helper.read_cache_candidate(pp)

                    push_count += 1
                    if push_count % 100000 == 0:
                        logger.info(f'model cache size: {len(self.model_cache)}')

                    if len(self.model_cache) < self.model_cache_max_length:
                        self.model_cache[ob] = p,v

                else:
                    pass


class ModelCacheClient:
    def __init__(self, pipe_pair:  PipePair):
        self.pipe_pair = pipe_pair
        self.helper = ModelCachePipeHelper()

    def query(self, ob):

        ob = ob.ravel()

        self.pipe_pair.open_read_nonblock()

        self.pipe_pair.open_write_nonblock()
        self.helper.write_cache_query(self.pipe_pair, ob.data, ob.nbytes)
        self.pipe_pair.close_write()

        r = self.helper.read_cache_query_result(self.pipe_pair)
        self.pipe_pair.close_read()

        if r:
            p,v = r
            p = np.frombuffer(p, dtype=np.float32)
            v = np.frombuffer(v, dtype=np.float32)
            v = v[0]
            r = p,v

        return r

    def suggest(self, ob, p, v):
        assert p.dtype == np.float32, p
        assert v.dtype == np.float32, p
        ob = ob.ravel()

        p = np.asarray(p, dtype=np.float32)
        p = p.ravel()

        v = np.asarray([v], dtype=np.float32)

        self.pipe_pair.open_write_nonblock()
        self.helper.write_cache_candidate(self.pipe_pair, ob.data, ob.nbytes, p.data, p.nbytes, v.data, v.nbytes)
        self.pipe_pair.close_write()

