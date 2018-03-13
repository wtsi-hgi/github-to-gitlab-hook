import unittest
from unittest.mock import MagicMock
import os
import json
import requests
import server
from tempfile import TemporaryDirectory
from git import Repo

from server.entrypoint import create_server
from server.wsgi_server import WsgiServerController


class TestEntrypoint(unittest.TestCase):

    def setUp(self):

        # Create the server and a controller to help start up and shutdown processes.
        test_server = create_server()
        self.server_controller = WsgiServerController(test_server)
        self.server_controller.start()

        # Set up two git remotes to act as test GitHub and GitLab.
        self.github_temp_dir = TemporaryDirectory()
        self.github_remote = Repo.init(self.github_temp_dir.name, bare=True)
        assert self.github_remote.bare

        self.gitlab_temp_dir = TemporaryDirectory()
        self.gitlab_remote = Repo.init(self.gitlab_temp_dir.name, bare=True)
        assert self.gitlab_remote.bare

    def tearDown(self):
        self.server_controller.stop()
        self.github_temp_dir.cleanup()
        self.gitlab_temp_dir.cleanup()

    def create_clone_repo_with_readme(self, url_of_repo_to_clone: str, location_of_clone: str):
        """
        This creates a clone of a remote so it can be used to pull and push easily.  It adds a README.txt so
        a change of state can be committed and pushed to the remote.

        :param url_of_repo_to_clone: can be a local git repo
        :param location_of_clone: can also be a local directory
        :return: a Bottle repository object for the cloned repo.
        """
        clone = Repo.clone_from(url_of_repo_to_clone, location_of_clone)
        assert clone.remotes['origin'].exists()
        clone.remotes['origin'].fetch()

        # Create a file in the cloned repo.
        new_file_path = os.path.join(location_of_clone, "README.txt")
        with open(new_file_path, 'w') as file:
            file.write("Hello world")

        # Add and commit the new file.
        clone.index.add([new_file_path])
        clone.index.commit("Adding README.txt")
        clone.commit()
        clone.remotes['origin'].push()

    def test_sync_github_to_gitlab(self):
        """
        Testing for a successful HTML response and that the contents of the GitHub test repo reached the
        GitLab test repo.

        :return:
        """

        with TemporaryDirectory() as temp_dir:
            # Intitalise a temp clone and push a readme to the GitHub test remote.
            self.create_clone_repo_with_readme(self.github_temp_dir.name, temp_dir)

        # Load test config to point to local test repos
        server.entrypoint.load_config = MagicMock(return_value={
            "github_repos": [self.github_temp_dir.name],
            "gitlab_url": self.gitlab_temp_dir.name
        })

        # JSON to use in the HTML request to the server.
        data = json.dumps({"repository": {"name": self.github_temp_dir.name, "url": self.gitlab_temp_dir.name}})

        # Capture and test the response.
        response = requests.post(self.server_controller.url, json=data,
                                 headers={'content-type': 'application/json'})
        self.assertEqual(200, response.status_code)
        # Todo: check that readme has successful passed from GitHub test repo to GitLab test repo.


if __name__ == '__main__':
    unittest.main()
