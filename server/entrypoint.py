"""
Copyright (c) 2017 Genome Research Ltd.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <http://www.gnu.org/licenses/>.
"""
"""
Entry point for the handling of GitHub pushes.
"""
import json
import os
import tempfile
import bottle
from git import Repo, Remote, PushInfo
from bottle import Bottle, LocalRequest, LocalResponse, response, request

from server.wsgi_server import WsgiServerController


def load_config(path: os.path):
    """
    Loads a json file used for config.  Handy to have the function separated for testing purposes.

    """
    with open(path) as file:
        json_config = json.load(file)
    return json_config


# The following functions are route handling for a local Bottle application.
def handle_github_push_request(req: LocalRequest, res: LocalResponse):
    """
    This checks the contents of the repositories_to_sync.json config file against the HTML request contents,
    specifically the name of the repo in the request, and if present, call the function to handle between github
    and gitlab.

    :param req: the Bottle.request which is the current request being handled by the server.
    :param res: the Bottle.response which is the current response being handled by the server.
    """

    # Find which Github repos should be synced.
    config = load_config(os.path.join(os.path.dirname(__file__), "../repositories_to_sync.json"))
    github_repos = config["github_repos"]

    # Check if message relates to a repo that should be synced.
    message = json.loads(req.json)
    repo_name = message["repository"]["name"]
    if repo_name not in github_repos:
        bottle.abort(404, "Repo not under GitLib")

    # Do the hard work of syncing.
    sync_github_repo_to_gitlab(repo_name, message["repository"]["url"], config["gitlab_url"])

    return res


def sync_github_repo_to_gitlab(repo_name: str, github_repo_url, gitlab_domain_url) -> [PushInfo]:
    """
    Create a temporary clone of the GitHub repo and set a remote to push to the associated GitLab repo.

    :param repo_name: the name of the repo from GitHub which should match an associated GitLab repo.
    :param github_repo_url: the location of the GitHub repo.
    :param gitlab_domain_url: the location of the GitLab domain where all the repos are.
    :return: Iterable list of push information.
             See: http://gitpython.readthedocs.io/en/stable/reference.html#git.remote.Remote.push
    """

    # Todo: get this to work with GitPython.  Failing that maybe use subprocess.

    # Create a temp directory to clone the repo to:
    with tempfile.TemporaryDirectory() as temp_dir:
        local_repo = Repo.clone_from(github_repo_url, temp_dir)
        gitlab_remote = local_repo.create_remote('gitlab', gitlab_domain_url + repo_name)
        assert gitlab_remote.exists()
        gitlab_remote.fetch()

        local_repo.commit()
    return gitlab_remote.push()


def create_server() -> Bottle:
    """
    Create the local Bottle app and assign routes.

    :return: Instance of bottle with defined routes.
    """

    app = Bottle()
    app.route(path="/", method="POST", callback=lambda: handle_github_push_request(request, response))

    return app


def run_server():
    server = create_server()
    server_controller = WsgiServerController(server, port=8080)
    server_controller.run()

if __name__ == "__main___":
    run_server()
