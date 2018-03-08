# Copyright (c) 2018 Genome Research Limited
# 
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import socket
from http.client import HTTPConnection
from threading import Thread, RLock, Event
from wsgiref.simple_server import make_server

from time import sleep


class ServerStateError(Exception):
    """
    Error raised if server is not in correct state for the action.
    """


class WsgiServerController:
    """
    WSGI server controller.
    """
    @staticmethod
    def _get_open_port() -> int:
        """
        Gets a PORT that will (probably) be available on the machine.
        It is possible that in-between the time in which the open PORT of found and when it is used, another process may
        bind to it instead.
        :return: the (probably) available PORT
        """
        free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        free_socket.bind(("", 0))
        free_socket.listen(1)
        port = free_socket.getsockname()[1]
        free_socket.close()
        return port

    @property
    def url(self) -> str:
        """
        The URL of the server.
        :return: server URL
        :raises ServerStateError: if the server is not running
        """
        if not self.running:
            raise ServerStateError("Server is not running")
        return f"http://{self.host}:{self.port}"

    @property
    def running(self) -> bool:
        """
        Whether the server is running.
        :return: `True` if the server is running
        """
        return self._server is not None

    def __init__(self, app, host: str="localhost", port: int=None):
        """
        Constructor.
        :param app: WSGI supported application
        :param host: the host the server should run on
        :param port: the port the server should bind to
        """
        self._app = app
        self._server = None
        self.host = host
        self.port = port
        self._start_event = Event()
        self._random_port = port is None
        self._state_lock = RLock()

    def run(self):
        """
        Runs the server (blocking).

        Not thread safe to be called directly!
        :raises ServerStateError: if the server is already running
        """
        if self.running:
            raise ServerStateError("Server is already running")
        self.port = self.port if not self._random_port else WsgiServerController._get_open_port()
        self._server = make_server(self.host, self.port, self._app)
        server_thread = Thread(target=self._server.serve_forever)
        server_thread.start()
        self._wait_for_start()
        self._start_event.set()
        server_thread.join()

    def start(self, block_until_started: bool=True):
        """
        Starts the server (non-blocking).

        Does nothing if the server is already running.
        :param block_until_started: blocks until the server has started if `True`
        """
        if not self.running:
            with self._state_lock:
                if not self.running:
                    Thread(target=self.run).start()
                    if block_until_started:
                        self._start_event.wait()

    def stop(self):
        """
        Stops the server.

        Does nothing if the server is already stopped
        """
        if self.running:
            with self._state_lock:
                if self.running:
                    self._server.shutdown()
                    self._server = None
                    self._start_event.clear()

    def _wait_for_start(self):
        """
        Blocks until the server has started.
        """
        while True:
            try:
                connection = HTTPConnection(self.host, self.port, timeout=1)
                connection.request("HEAD", "/")
                connection.getresponse()
                break
            except socket.timeout:
                sleep(0.1)
