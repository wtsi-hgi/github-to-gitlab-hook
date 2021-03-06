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
import configargparse
import json
import logging
import os
import tempfile
from typing import List

import bottle
import mattermost_log_handler
import requests
from bottle import Bottle, LocalRequest, LocalResponse, request, response
from git import PushInfo, Remote, Repo, GitCommandError
import git

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


def load_config(path: str):
    """
    Loads a json file used for config.  Handy to have the function separated for testing purposes.

    """
    with open(path) as file:
        json_config = json.load(file)
    return json_config

def get_ghgl_response(status_code, message):
    return bottle.HTTPResponse(
        body=json.dumps({
            "message": message
        }),
        status=status_code
    )


# The following functions are route handling for a local Bottle application.
def handle_github_push_request(req: LocalRequest, res: LocalResponse, gitlab_base_url: str) -> LocalResponse:
    """
    This checks the contents of the config.json config file against the HTML request contents,
    specifically the name of the repo in the request, and if present, call the function to handle between github
    and gitlab.

    :param req: the Bottle.request which is the current request being handled by the server.
    :param res: the Bottle.response which is the current response being handled by the server.
    """
    if req.headers.get("X-GitHub-Event", None) != "push":
        return get_ghgl_response(200, "No action. Event is not a push event.")

    if req.json is None:
        logger.error("Cannot parse request body as JSON.")
        return get_ghgl_response(400, "Can't proceed. Request body is not JSON.")

    # Check if message relates to a repo that should be synced.
    message = req.json
    repo_name = message["repository"]["name"]

    # Do the hard work of syncing.
    return sync_github_repo_to_gitlab(repo_name, message["repository"]["clone_url"], gitlab_base_url)


def sync_github_repo_to_gitlab(repo_name: str, github_repo_url: str, gitlab_base_url: str) -> None:
    """
    Create a temporary clone of the GitHub repo and set a remote to push to the associated GitLab repo.

    :param repo_name: the name of the repo from GitHub which should match an associated GitLab repo.
    :param github_repo_url: the location of the GitHub repo.
    :param gitlab_base_url: the location of the GitLab domain where all the repos are.
    :return: Iterable list of push information.
             See: http://gitpython.readthedocs.io/en/stable/reference.html#git.remote.Remote.push
    """

    # Create a temp directory to clone the repo to:
    with tempfile.TemporaryDirectory() as temp_dir:
        local_repo = Repo.clone_from(github_repo_url, temp_dir)
        gitlab_repo = os.path.join(gitlab_base_url, repo_name)
        gitlab_remote = local_repo.create_remote('gitlab', gitlab_repo)

        g = git.cmd.Git()
        try:
            g.ls_remote(gitlab_repo)
        except GitCommandError:
            logger.exception(f"Corresponding GitLab repo {gitlab_repo} not found")
            return get_ghgl_response(500, f"Corresponding GitLab repo {gitlab_repo} not found.")

        logger.info("attempting to sync to gitlab remote %s\n" % gitlab_repo)
        push_infos = gitlab_remote.push()

        push_errors = []

        if len(push_infos) == 0:
            logger.error(f"Failed to push to GitLab repo {gitlab_repo}")
            return get_ghgl_response(500, f"Failed to push to GitLab repo {gitlab_repo}")

        for push_info in push_infos:
            if push_info.flags & PushInfo.ERROR:
                push_errors.append(f"Pushing to {push_info.remote_ref} failed: {push_info.summary}")

        if push_errors:
            errors_str = "\n".join(push_errors)
            error_text = f"Failed to push to GitLab.\n{errors_str}"
            logger.error(error_text)
            return get_ghgl_response(500, error_text)

        return get_ghgl_response(201, "Repository synced.")

def create_server(gitlab_base_url) -> Bottle:
    """
    Create the local Bottle app and assign routes.

    :return: Instance of bottle with defined routes.
    """
    def handle_bottle_request():
        try:
            return handle_github_push_request(request, response, gitlab_base_url)
        except Exception as exp:
            logger.exception("Exception in routing to endpoint")
            raise exp

    app = Bottle()
    app.route(path="/", method="POST", callback=handle_bottle_request)

    return app


def main():
    parser = configargparse.ArgumentParser()
    parser.add_argument("--port", default=8080, type=int)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--config-file", is_config_file=True, help="Config file for the options below. (dashes should be underscores).")
    parser.add_argument("--gitlab-base-url", required=True, help="Base URL to sync all repositories to.")
    parser.add_argument("--mattermost-webhook-url", help="If set, sets the mattermost webhook endpoint to send logs to.")
    opts = parser.parse_args()

    if opts.mattermost_webhook_url is not None:
        mm_handler = mattermost_log_handler.MattermostLogHandler(opts.mattermost_webhook_url, username="Github to Gitlab logs")
        mm_handler.setLevel(logging.WARNING)
        logging.getLogger().addHandler(mm_handler)

    server = create_server(opts.gitlab_base_url)
    server.run(server="tornado", port=opts.port, host=opts.host)

if __name__ == "__main__":
    main()
