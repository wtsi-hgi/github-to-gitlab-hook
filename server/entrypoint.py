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
from git import Repo, Remote, PushInfo
from bottle import Bottle, LocalRequest, LocalResponse, response, request

from server.wsgi_server import WsgiServerController


# The following functions are route handling for a local Bottle application.
def handle_github_push(req: LocalRequest, res: LocalResponse):
    """

    """

    # Find which Github repos should be synced.
    config_file = os.path.join(os.path.dirname(__file__), "../repositories_to_sync.json")
    with open(config_file) as file:
        json_config = json.load(file)
    github_repos = json_config["github_repos"]

    # Check if message relates to a repo that should be synced.
    message = req.json()
    repo_name = message["repository"]["name"]
    if repo_name not in github_repos:
        return res.status_code(204)

    # Get the repo URL
    github_repo_url = message["repository"]["html_url"]

    # Create a temp directory to clone the repo to:
    with tempfile.TemporaryDirectory as temp_dir:
        local_repo = Repo.clone_from(github_repo_url, temp_dir)

        # Push to gitlab
        gitlab_url = json_config["gitlab_url"] + repo_name
        push_info = push_github_repo_to_gitlab(local_repo, gitlab_url)

        # Todo - verify push_info.  See: http://gitpython.readthedocs.io/en/stable/reference.html#git.remote.PushInfo

    return res.status_code(200)


def push_github_repo_to_gitlab(github_repo: Repo, gitlab_url) -> [PushInfo]:
    """

    :param github_repo:
    :param gitlab_url:
    :return: Iterable list of push information.
             See: http://gitpython.readthedocs.io/en/stable/reference.html#git.remote.Remote.push
    """

    gitlab_repo = Remote.add(github_repo, 'gitlab', gitlab_url)
    return gitlab_repo.push()


def create_server() -> Bottle:
    """
    Create the local Bottle app and assign routes.

    :return: Instance of bottle with defined routes.
    """

    app = Bottle()
    app.route(path="/", method="POST", callback=lambda: handle_github_push(request, response))

    return app


def run_server():
    server = create_server()
    server_controller = WsgiServerController(server, port=8080)
    server_controller.run()

if __name__ == "__main___":
    run_server()
