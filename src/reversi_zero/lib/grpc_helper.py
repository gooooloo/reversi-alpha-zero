import grpc

from src.reversi_zero.lib import chunk_pb2
from src.reversi_zero.lib import chunk_pb2_grpc

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

    def download_model_config(self, out_file_name):
        response = self.stub.download_model_config(chunk_pb2.Empty())
        save_chunks_to_file(response, out_file_name)

    def download_model_weight(self, out_file_name):
        response = self.stub.download_model_weight(chunk_pb2.Empty())
        save_chunks_to_file(response, out_file_name)

    def report_resign_ctrl(self, resignCtrl):
        self.stub.report_resign_ctrl(resignCtrl)

    def ask_resign_threshold(self):
        self.stub.ask_resign_threshold(chunk_pb2.Empty())

