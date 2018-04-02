import glob
import os
import shutil
from concurrent import futures
from logging import getLogger

import grpc
import time

from src.reversi_zero.config import Config
from src.reversi_zero.lib import chunk_pb2
from src.reversi_zero.lib import chunk_pb2_grpc
from src.reversi_zero.lib.data_helper import remove_old_play_data

CHUNK_SIZE = 1024 * 1024  # 1MB

logger = getLogger(__name__)


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


def modelstep_to_simplestring(modelstep):
    return f'{modelstep.type}_{modelstep.step}'


def simplestring_to_modelstep(modelstep):
    t,s = modelstep.split('_')
    return chunk_pb2.ModelStep(type=t, step=s)

MODEL_STEP_TYPE_NEWEST  = 'N'
MODEL_STEP_TYPE_ARCHIVE = 'A'
MODEL_STEP_TYPE_TO_EVAL = 'E'

class GrpcClient:
    def __init__(self, config):
        address = f'{config.ipc.fs_ip}:{config.ipc.fs_port}'
        channel = grpc.insecure_channel(address)
        logger.info(f'address:{address}')
        self.stub = chunk_pb2_grpc.FileServerStub(channel)

    def upload_play_data(self, play_data):
        self.stub.upload_play_data(play_data)

    def download_model_config(self, out_file_name, model_step):
        response = self.stub.download_model_config(model_step)
        save_chunks_to_file(response, out_file_name)

    def download_model_weight(self, out_file_name, model_step):
        response = self.stub.download_model_weight(model_step)
        save_chunks_to_file(response, out_file_name)

    def list_model_steps_to_eval(self):
        response = self.stub.list_model_steps_to_eval(chunk_pb2.Empty())
        return [step.step for step in response]

    def list_model_steps_archive(self):
        response = self.stub.list_model_steps_archive(chunk_pb2.Empty())
        return [step.step for step in response]

    def report_better_model(self, model_step):
        self.stub.report_better_model(model_step)

    def remove_model(self, model_step):
        self.stub.remove_model(model_step)

    def report_resign_false_positive(self, resign_fp):
        self.stub.report_resign_false_positive(resign_fp)

    def ask_resign_v(self):
        return self.stub.ask_resign_v(chunk_pb2.Empty())


class GrpcServer(chunk_pb2_grpc.FileServerServicer):
    def __init__(self, config : Config):
        self.config = config
        self.play_data = []
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chunk_pb2_grpc.add_FileServerServicer_to_server(self, self.server)

    # servicer api implementation
    def upload_play_data(self, request_iterator, context):
        logger.info('upload_play_data')
        from src.reversi_zero.lib.data_helper import save_play_data
        for move in request_iterator:
            self.play_data.append(move)

            if len(self.play_data) >= self.config.play_data.nb_move_in_file:
                save_play_data(self.config.resource, self.play_data)
                remove_old_play_data(self.config)
                self.play_data = []

        logger.info('upload_play_data done')
        return chunk_pb2.Empty()

    # servicer api implementation
    def download_model_config(self, request, context):
        logger.info('download_model_config')

        rc = self.config.resource
        p = {
            MODEL_STEP_TYPE_NEWEST: self.config.resource.model_config_path,
            MODEL_STEP_TYPE_TO_EVAL: os.path.join(rc.to_eval_model_dir,
                                                  rc.to_eval_model_dirname_tmpl % request.step,
                                                  rc.model_weight_filename),
            MODEL_STEP_TYPE_ARCHIVE: os.path.join(rc.archive_model_dir,
                                                  rc.archive_model_dirname_tmpl % request.step,
                                                  rc.model_config_filename)
        }[request.type]
        return get_file_chunks(p)

    # servicer api implementation
    def download_model_weight(self, request, context):
        logger.info('download_model_weight_now')

        rc = self.config.resource
        p = {
            MODEL_STEP_TYPE_NEWEST: self.config.resource.model_weight_path,
            MODEL_STEP_TYPE_TO_EVAL: os.path.join(rc.to_eval_model_dir,
                                                  rc.to_eval_model_dirname_tmpl % request.step,
                                                  rc.model_weight_filename),
            MODEL_STEP_TYPE_ARCHIVE: os.path.join(rc.generation_model_dir,
                                                  rc.generation_model_dirname_tmpl % request.step,
                                                  rc.model_weight_filename)
        }[request.type]
        return get_file_chunks(p)

    # servicer api implementation
    def list_model_steps_to_eval(self, request, context):
        logger.info('list_model_steps_to_eval')

        rc = self.config.resource
        pattern = os.path.join(rc.to_eval_model_dir, rc.to_eval_model_dirname_tmpl.replace('%s','*'))
        for p in glob.glob(pattern):
            step = p[len(pattern.split('*')[0]):-len(pattern.split('*')[1])]
            step = int(step)
            yield chunk_pb2.ModelStep(step=step)

    # servicer api implementation
    def list_model_steps_to_archive(self, request, context):
        logger.info('list_model_steps_to_archive')

        rc = self.config.resource
        pattern = os.path.join(rc.generation_model_dir, rc.generation_model_dirname_tmpl.replace('%s','*'))
        for p in glob.glob(pattern):
            step = p[len(pattern.split('*')[0]):-len(pattern.split('*')[1])]
            step = int(step)
            yield chunk_pb2.ModelStep(step=step)

    def report_better_model(self, request, context):
        logger.info('report_better_model')
        assert request.type == MODEL_STEP_TYPE_TO_EVAL
        rc = self.config.resource
        to_eval_model_dir = os.path.join(rc.to_eval_model_dir, rc.to_eval_model_dirname_tmpl % request.step)
        to_eval_config = os.path.join(to_eval_model_dir, rc.model_config_filename),
        to_eval_weight = os.path.join(to_eval_model_dir, rc.model_weight_filename),
        shutil.copyfile(to_eval_config, rc.model_config_path)
        shutil.copyfile(to_eval_weight, rc.model_weight_path)
        shutil.move(to_eval_model_dir, rc.generation_model_dir)

    def remove_model(self, request, context):
        logger.info('remove_model')
        assert request.type == MODEL_STEP_TYPE_TO_EVAL
        rc = self.config.resource
        to_eval_model_dir = os.path.join(rc.to_eval_model_dir, rc.to_eval_model_dirname_tmpl % request.step)
        shutil.rmtree(to_eval_model_dir, ignore_errors=True)

    # servicer api implementation
    def report_resign_false_positive(self, request, context):
        logger.info('report_resign_false_positive')
        from src.reversi_zero.lib.resign_helper import handle_resign_false_positive_delta
        handle_resign_false_positive_delta(self.config, request)
        return chunk_pb2.Empty()

    # servicer api implementation
    def ask_resign_v(self, request, context):
        logger.info('ask_resign_v')
        from src.reversi_zero.lib.resign_helper import decide_resign_v_once
        return decide_resign_v_once(self.config)

    def start(self):
        self.server.add_insecure_port(f'[::]:{self.config.ipc.fs_port}')
        self.server.start()
        logger.info(f'grpc start started. port:{self.config.ipc.fs_port}')

        try:
            while True:
                time.sleep(60*60*24)
        except KeyboardInterrupt:
            self.server.stop(0)
