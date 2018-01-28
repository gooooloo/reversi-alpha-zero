from logging import getLogger

import requests
from src.reversi_zero.lib.gtp import GTPClient

logger = getLogger(__name__)


class HttpClient(GTPClient):
    def __init__(self, url):
        super().__init__(pipe_pair=None)
        self.url = url

    def send(self, data):
        postdata = data
        response = requests.post(self.url, postdata)
        return response.text


class HttpServer:
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
