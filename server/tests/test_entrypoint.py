import unittest
from unittest.mock import MagicMock
import os
import json
import requests
import server

from server.entrypoint import create_server
from server.wsgi_server import WsgiServerController


class TestEntrypoint(unittest.TestCase):

    def setUp(self):
        print("Set up")  # debug
        test_server = create_server()
        self.server_controller = WsgiServerController(test_server)
        self.server_controller.start()

        # Load test config to point to local test repos
        server.entrypoint.load_config = MagicMock(return_value={
            "github_repos": ["the_repo"],
            "gitlab_url": os.path.join(os.path.dirname(__file__), "gitlab_test_repo/")
        })


    def tearDown(self):
        print("Tear down") # debug
        self.server_controller.stop()

    def test_response(self):
        print("Starting test_response")  # debug

        data = json.dumps({
            "repository": {
                "name": "the_repo",
                "url": os.path.join(os.path.dirname(__file__), "github_test_repo/the_repo")
            }
        })

        response = requests.post(self.server_controller.url, json=data, headers={'content-type': 'application/json'})
        self.assertEqual(200, response.status_code)


if __name__ == '__main__':
    unittest.main()
