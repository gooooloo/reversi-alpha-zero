# lots of codes borrowed from https://gist.github.com/bradmontgomery/2219997
import json
import os
from logging import getLogger

import requests

from src.reversi_zero.lib.data_helper import save_play_data, remove_old_play_data
from src.reversi_zero.lib.gtp import GTPClient
from src.reversi_zero.lib.resign_helper import handle_resign_ctrl_delta

logger = getLogger(__name__)


class HttpPlayClient(GTPClient):
    def __init__(self, url):
        super().__init__(pipe_pair=None)
        self.url = url

    def send(self, data):
        postdata = data
        response = requests.post(self.url, postdata)
        return response.text


class HttpPlayServer:
    def __init__(self, pipe_pair, port):
        self.gtp_client = gtp_client = GTPClient(pipe_pair)
        self.port = port

        from http.server import BaseHTTPRequestHandler, HTTPServer

        class S(BaseHTTPRequestHandler):
            def _set_headers(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()

            def do_POST(self):
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode()
                logger.info(f'http get POST data: {post_data}')
                result = gtp_client.send(post_data)
                self._set_headers()
                self.wfile.write(result.encode())

        server_address = ('', self.port)
        self.httpd = HTTPServer(server_address, S)

    def start(self):
        print('Starting httpd...')
        self.httpd.serve_forever()


class HttpFileServer:
    def __init__(self, config):
        cr = config.resource

        from http.server import BaseHTTPRequestHandler, HTTPServer

        class S(BaseHTTPRequestHandler):

            def do_GET(self):
                if self.path == cr.remote_model_config_path:
                    self._write_file(cr.model_config_path)

                elif self.path == cr.remote_model_weight_path:
                    self._write_file(cr.model_weight_path)

                elif self.path == cr.remote_resign_path:
                    self._write_file(cr.resign_log_path)

                else:
                    logger.info(f'unknown GET path {self.path}')

            def _write_file(self, fn):
                with open(fn, 'wb') as f:
                    data = f.readall()

                self.send_response(200)
                self.send_header('Content-type', 'text/octet-stream')
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)

                if self.path == cr.remote_resign_path:
                    d = json.loads(post_data.decode())
                    handle_resign_ctrl_delta(config, d)

                elif self.path == cr.remote_play_data_path:
                    save_play_data(cr, post_data)
                    remove_old_play_data(config)

                else:
                    logger.info(f'unknown POST path {self.path}')
                    return

                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write('OK'.encode())

        server_address = ('', config.opts.port)
        self.httpd = HTTPServer(server_address, S)

    def start(self):
        print('Starting httpd...')
        self.httpd.serve_forever()
