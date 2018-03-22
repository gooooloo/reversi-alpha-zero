from concurrent import futures

import grpc
import time

from src.reversi_zero.lib import chunk_pb2
from src.reversi_zero.lib import chunk_pb2_grpc
from src.reversi_zero.config import Config

from logging import getLogger

from src.reversi_zero.lib.grpc_helper import get_file_chunks

logger = getLogger(__name__)


def start(config: Config):
    FileServer(config).start()


class FileServer(chunk_pb2_grpc.FileServerServicer):
    def __init__(self, config : Config):
        self.config = config
        self.play_data = []
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        chunk_pb2_grpc.add_FileServerServicer_to_server(self, self.server)

    # servicer api implementation
    def upload_play_data(self, request_iterator, context):
        from src.reversi_zero.lib.data_helper import save_play_data
        for move in request_iterator:
            self.play_data.append([move.cob, move.pi, move.z])

        if len(self.play_data) > self.config.play_data.nb_game_in_file:
            save_play_data(self.config.resource, self.play_data)
            self.play_data = []

        return chunk_pb2.Empty()

    # servicer api implementation
    def download_model_config(self, request, context):
        return get_file_chunks(self.config.resource.model_config_path)

    # servicer api implementation
    def download_model_weight(self, request, context):
        return get_file_chunks(self.config.resource.model_weight_path)

    # servicer api implementation
    def report_resign_ctrl(self, request, context):
        from src.reversi_zero.lib.resign_helper import ResignCtrl
        from src.reversi_zero.lib.resign_helper import handle_resign_ctrl_delta
        delta = ResignCtrl(request.n, request.f_p_n)
        handle_resign_ctrl_delta(self.config, delta)

    # servicer api implementation
    def ask_resign_threshold(self, request, context):
        from src.reversi_zero.lib.resign_helper import compute_resign_v
        enabled, v = compute_resign_v(self.config)
        return chunk_pb2.ResignThreshold(enabled=enabled, v=v)

    def start(self):
        self.server.add_insecure_port(f'[::]:{self.config.opts.http_port}')
        self.server.start()

        try:
            while True:
                time.sleep(60*60*24)
        except KeyboardInterrupt:
            self.server.stop(0)
