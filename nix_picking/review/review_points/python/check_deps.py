from typing import final, override, Any
import re
from nix_manipulator.parser import parse_to_ast
import toml
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

        # Determine repo
        try:
            if file_content["src"]["function"] == "fetchFromGitHub":
                owner = file_content["src"]["owner"]
                repo = file_content["src"]["repo"]
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

        # Get and parse deps file from the repo
        deps_files = self.__get_python_deps_files(owner, repo)
        deps: set[str] = set()
        if not deps_files:
            print("No requirements.txt or pyproject.toml file found in the repository.")
        if "pyproject.toml" in deps_files:
            pyproject: dict[str, Any] = toml.loads(deps_files["pyproject.toml"])
            try:
                for dependency_str in pyproject["project"]["dependencies"]:
                    dependency = re.split(r'[>=<~!,;]', dependency_str)[0].strip()
                    deps.add(dependency)
            except KeyError:
                print("No dependencies found in pyproject.toml file.")
        if "requirements.txt" in deps_files:
            requirements = deps_files["requirements.txt"].splitlines()
            deps = deps.union(set(requirements))

        # Get deps from the Nix file
        try:
            nix_file_deps = set(file_content["dependencies"])
        except KeyError:
            print("No dependencies found in the Nix file.")
            nix_file_deps = set()

        # Compare
        if deps != nix_file_deps:
            print(
                "CAUTION: The dependencies in the Nix file do not match the dependencies found in the repository."
            )
            print(f"Dependencies in the repository: {deps}")
            print(f"Dependencies in the Nix file: {nix_file_deps}")
            return False

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
    from nix_picking.parser import NixParser

    rev = checkDeps()
    with open("tests/inputs/python/a2a-sdk/default.nix") as f:
        file_content = f.read()
    parser = NixParser()
    parsed_file = parser.parse(file_content, additional_levels=2)
    rev.apply(parsed_file)
