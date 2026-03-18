import os
from typing import final
from contextlib import contextmanager
from github import (
    Github,
    Auth,
    GithubException,
    UnknownObjectException,
)
from github.Repository import Repository
from github.PullRequest import PullRequest

BLACK_LISTED_FILES = {
    "pkgs/top-level/python-packages.nix",
    "maintainers/maintainer-list.nix",
    "pkgs/by-name/hy/hyprland/info.json",
}

@final
class GitHubService:

    def __init__(self, env_var_name: str = "ACCESS_TOKEN"):
        self.env_var_name = env_var_name

    @contextmanager
    def get_github_client(self):
        """Context manager to get a GitHub client using an access token from environment variables."""
        GITHUB_ACCESS_TOKEN = os.environ.get(self.env_var_name)
        if not GITHUB_ACCESS_TOKEN:
            raise ValueError(self.env_var_name + " environment variable is not set")
        auth = Auth.Token(GITHUB_ACCESS_TOKEN)
        with Github(auth=auth) as g:
            yield g
