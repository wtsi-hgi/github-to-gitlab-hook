import unittest

import requests

from server.examples.example import create_example_app, HELLO_WORLD_TEXT
from server.examples.wsgi_server import WsgiServerController


class TestExampleApp(unittest.TestCase):
    def setUp(self):
        app = create_example_app()
        self.server_controller = WsgiServerController(app)
        self.server_controller.start()

    def tearDown(self):
        self.server_controller.stop()

    def test_root_endpoint(self):
        response = requests.get(f"{self.server_controller.url}/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(HELLO_WORLD_TEXT, response.text)


if __name__ == "__main__":
    unittest.main()
