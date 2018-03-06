import unittest
from threading import Thread
from time import sleep

import requests

from server.entrypoint import run_server


class TestEntrypoint(unittest.TestCase):

    def setUp(self):
        Thread(target=run_server).start()
        sleep(2)

    def test_response(self):

        response = requests.post('http://localhost:8080/', data={"key1":"value1", "key2":"value2"})
        self.assertEqual("SUCCESS", response.text)
        self.assertEqual(200, response.status_code)


if __name__ == '__main__':
    unittest.main()
