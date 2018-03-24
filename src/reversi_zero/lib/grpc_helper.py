from concurrent import futures

import grpc
import time

from src.reversi_zero.config import Config
from src.reversi_zero.lib import chunk_pb2
from src.reversi_zero.lib import chunk_pb2_grpc
from src.reversi_zero.lib.data_helper import remove_old_play_data

CHUNK_SIZE = 1024 * 1024  # 1MB


def get_buffer_chunks(buffer):
    for p in range(0, len(buffer), CHUNK_SIZE):
        piece = buffer[p:p+CHUNK_SIZE]
        if len(piece) == 0:
            return
        yield chunk_pb2.Chunk(buffer=piece)


def get_file_chunks(filename):
    with open(filename, 'rb') as f:
        while True:
            piece = f.read(CHUNK_SIZE);
            if len(piece) == 0:
                return
            yield chunk_pb2.Chunk(buffer=piece)


def save_chunks_to_file(chunks, filename):
    with open(filename, 'wb') as f:
        for chunk in chunks:
            f.write(chunk.buffer)


class FileClient:
    def __init__(self, config):
        channel = grpc.insecure_channel(f'{config.opts.http_url}:{config.opts.http_port}')
        self.stub = chunk_pb2_grpc.FileServerStub(channel)

    def upload_play_data(self, play_data):
        self.stub.upload_play_data(play_data)

    def download_model_config(self, out_file_name, model_generation):
        response = self.stub.download_model_config(chunk_pb2.ModelGeneration(generation=model_generation))
        save_chunks_to_file(response, out_file_name)

    def download_model_weight(self, out_file_name, model_generation):
        response = self.stub.download_model_weight(chunk_pb2.ModelGeneration(generation=model_generation))
        save_chunks_to_file(response, out_file_name)

    def report_resign_false_positive(self, resign_fp):
        self.stub.report_resign_false_positive(resign_fp)

    def ask_resign_v(self):
        self.stub.ask_resign_v(chunk_pb2.Empty())


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
            remove_old_play_data(self.config)
            self.play_data = []

        return chunk_pb2.Empty()

    # servicer api implementation
    def download_model_config(self, request, context):
        # TODO: check request.generation
        return get_file_chunks(self.config.resource.model_config_path)

    # servicer api implementation
    def download_model_weight(self, request, context):
        # TODO: check request.generation
        return get_file_chunks(self.config.resource.model_weight_path)

    # servicer api implementation
    def report_resign_False_Positive(self, request, context):
        from src.reversi_zero.lib.resign_helper import handle_resign_false_positive_delta
        handle_resign_false_positive_delta(self.config, request)
        return chunk_pb2.Empty()

    # servicer api implementation
    def ask_resign_v(self, request, context):
        from src.reversi_zero.lib.resign_helper import decide_resign_v_once
        return decide_resign_v_once(self.config)

    def start(self):
        self.server.add_insecure_port(f'[::]:{self.config.opts.http_port}')
        self.server.start()

        try:
            while True:
                time.sleep(60*60*24)
        except KeyboardInterrupt:
            self.server.stop(0)
