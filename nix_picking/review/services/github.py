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

    def fetch_pull_request_files(
        self, pr_number: int, repo_full_name: str
    ) -> dict[str, str]:
        pr_file_contents: dict[str, str] = {}
        try:
            with self.get_github_client() as g:
                repo: Repository = g.get_repo(repo_full_name)
                pr: PullRequest = repo.get_pull(pr_number)
                files = pr.get_files()
                for file in files:
                    if file.filename in BLACK_LISTED_FILES:
                        continue
                    files_content = repo.get_contents(file.filename, ref=pr.head.sha)
                    pr_file_contents[file.filename] = files_content.decoded_content.decode("utf-8")
                return pr_file_contents
        except UnknownObjectException as e:
            raise ValueError(
                f"Pull request #{pr_number} not found in repository {repo_full_name}"
            )
        except GithubException as e:
            raise ValueError(f"GitHub API error: {e.data.get('message', str(e))}")
