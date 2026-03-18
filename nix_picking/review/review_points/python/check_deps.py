from typing import final, override, Any

from github import GithubException
from nix_picking.review.review_points.enums import Topics
from nix_picking.review.review_points.base import ReviewPointBase
from nix_picking.review.services.github import GitHubService


@final
class checkDeps(ReviewPointBase):
    @override
    def __init__(self):
        super().__init__()
        self._topic = Topics.PYTHON
        self._importance = 5
        self._explanation = "Check if the project has a requirements.txt or pyproject.toml file to manage dependencies."
        self._source = (
            "https://nixos.org/manual/nixpkgs/stable/#buildpythonpackage-function"
        )

    @override
    def apply(self, file_content: dict[str, Any]) -> bool:
        owner, repo, tag = None, None, None
        try:
            if file_content["src"]["function"] == "fetchFromGitHub":
                owner = file_content["src"]["owner"]
                repo = file_content["src"]["repo"]
                tag = file_content["src"]["tag"]
            elif "github" in file_content["meta"]["homepage"].split("/"):
                github_url = file_content["meta"]["homepage"]
                parts = github_url.split("/")
                owner = parts[3]
                repo = parts[4]
            if not owner or not repo:
                raise ValueError(
                    "Could not determine GitHub repository from file content"
                )
        except ValueError:
            return False
        except KeyError:
            return False

        files = self.__get_python_deps_files(owner, repo)
        print(files)
        # here

        return True

    def __get_python_deps_files(self, owner: str, repo: str) -> dict[str, str]:
        """Check if the repository has a requirements.txt or pyproject.toml file."""
        github_service = GitHubService()
        deps_files = {"pyproject.toml", "requirements.txt"}
        files = {}
        with github_service.get_github_client() as g:
            try:
                repository = g.get_repo(f"{owner}/{repo}")
                for deps_file in deps_files:
                    try:
                        content = repository.get_contents(deps_file)
                        files[deps_file] = content.decoded_content.decode("utf-8")
                        print(f"Found {deps_file} in the repository.")
                    except GithubException:
                        continue
            except GithubException:
                print("Repository not found or access denied.")
            except Exception as e:
                print(f"Error fetching repository contents: {e}")
            return files


if __name__ == "__main__":
    import json

    rev = checkDeps()
    with open("tests/outputs/python/a2a-sdk/default.json") as f:
        file_content = json.load(f)
        rev.apply(file_content)
