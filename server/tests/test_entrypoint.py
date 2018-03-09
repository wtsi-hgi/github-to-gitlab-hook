import unittest
import os
import json
import requests

from server.entrypoint import create_server
from server.wsgi_server import WsgiServerController


class TestEntrypoint(unittest.TestCase):

    def setUp(self):
        server = create_server()
        self.server_controller = WsgiServerController(server)
        self.server_controller.start()


    def tearDown(self):
        self.server_controller.stop()

    def test_response(self):

        data = json.dumps({
            "repository": {
                "name": "the_repo",
                "html_url": os.path.dirname(__file__) + "github_test_repo/"
            }
        })

        response = requests.post('file://', data)
        self.assertEqual(200, response.status_code)


if __name__ == '__main__':
    unittest.main()
