import unittest
from unittest.mock import MagicMock
import os
import json
import requests
import github2gitlab
import time
from tempfile import TemporaryDirectory
from git import Repo

from github2gitlab import create_server
from github2gitlab.wsgi_server import WsgiServerController


class TestEntrypoint(unittest.TestCase):

    def setUp(self):
        # Set up two directories to act as test GitHub and GitLab.
        self.github_temp_dir = TemporaryDirectory(prefix="github-repo-")
        self.gitlab_temp_dir = TemporaryDirectory(prefix="gitlab-repo-")

        # Create the server and a controller to help start up and shutdown processes.
        test_server = create_server(self.gitlab_temp_dir.name)
        self.server_controller = WsgiServerController(test_server)
        self.server_controller.start()

    def tearDown(self):
        self.server_controller.stop()
        self.github_temp_dir.cleanup()
        self.gitlab_temp_dir.cleanup()

    def create_bare_repo(self, location: str, name: str):
        repo_path = os.path.join(location, name)
        repo = Repo.init(repo_path, bare=True)
        assert repo.bare
        return repo_path

    def add_readme(self, repo: str):
        with TemporaryDirectory() as location_of_clone:
            clone = Repo.clone_from(repo, location_of_clone)
            assert clone.remotes['origin'].exists()
            clone.remotes['origin'].fetch() # needed?

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
        test_repo_name = "testrepo"
        github_repo = self.create_bare_repo(self.github_temp_dir.name, test_repo_name)
        self.create_bare_repo(self.gitlab_temp_dir.name, test_repo_name)
        self.add_readme(github_repo)

        # JSON to use in the HTML request to the server.
        data = json.dumps({
            "repository": {
                "name": test_repo_name,
                "clone_url": github_repo
            }
        })

        # Capture and test the response.
        response = requests.post(
            self.server_controller.url,
            data=data,
            headers={
                'content-type': 'application/json',
                "X-GitHub-Event": "push"
            }
        )

        self.assertEqual(201, response.status_code)
        # assert a master branch exists (would happen after the sync)
        self.assertTrue(
            os.path.isfile(os.path.join(self.gitlab_temp_dir.name, test_repo_name, "refs", "heads", "master")),
            f"No master branch exists in test repo {github_repo}"
        )


if __name__ == '__main__':
    unittest.main()
