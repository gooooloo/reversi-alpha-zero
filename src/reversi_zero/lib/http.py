# lots of codes borrowed from https://gist.github.com/bradmontgomery/2219997
from logging import getLogger

import requests
from src.reversi_zero.lib.gtp import GTPClient

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


class HttpFileClient(GTPClient):
    def __init__(self, url):
        super().__init__(pipe_pair=None)
        self.url = url
        self.play_data_url = url + '/play_data'
        self.model_url = url + '/model'
        self.resign_url = url + '/model'

    def post_play_file_path_file(self, data):
        return self.post(self.play_file_path_url, data)

    def post_model_file(self, file_path):
        return self.post(self.model_url, file_path)

    def post_resign_file(self, file_path):
        return self.post(self.resign_url, file_path)

    def get_play_data_file(self):
        return self.get(self.play_data_url)

    def get_model_file(self):
        return self.get(self.model_url)

    def get_resign_file(self):
        return self.get(self.resign_url)

    def post(self, url, data):
        postdata = data
        response = requests.post(url, postdata)
        return response.text

    def get(self, url):
        response = requests.get(url)
        return response.text


class HttpFileServer:
    def __init__(self, folder, port):
        self.port = port

        from http.server import BaseHTTPRequestHandler, HTTPServer

        class S(BaseHTTPRequestHandler):

            def do_GET(self):
                file_name = self.headers['File-Name']

                import os
                with open(os.path.join(folder, file_name), 'wb') as f:
                    data = f.readall()

                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                content_length = int(self.headers['Content-Length'])
                file_name = self.headers['File-Name']
                post_data = self.rfile.read(content_length).decode()

                import os
                with open(os.path.join(folder, file_name), 'wb') as f:
                    f.write(post_data)

                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write('OK'.encode())

            def do_DELETE(self):
                file_name = self.headers['File-Name']

                import os
                if os.path.exists(os.path.join(folder, file_name)):
                    os.remove(os.path.join(folder, file_name))

                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write('OK'.encode())

        server_address = ('', self.port)
        self.httpd = HTTPServer(server_address, S)

    def start(self):
        print('Starting httpd...')
        self.httpd.serve_forever()
