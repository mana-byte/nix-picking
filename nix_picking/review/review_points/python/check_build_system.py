from typing import final, override, Any
import re
import toml
from github import GithubException

from nix_picking.review.review_points.base import ReviewPointBase
from nix_picking.review.services.github import GitHubService


@final
class CheckBuildSystem(ReviewPointBase):
    @override
    def __init__(self):
        super().__init__()
        self._importance = 5
        self._explanation = "Check build-system in pyproject.toml"
        self._source = (
            "https://nixos.org/manual/nixpkgs/stable/#buildpythonpackage-function"
        )

    @override
    def apply(self, file_content: dict[str, Any]) -> bool:
        owner, repo, version = None, None, ""

        # Determine repo
        try:
            if file_content["src"]["function"] == "fetchFromGitHub":
                owner = file_content["src"]["owner"]
                repo = file_content["src"]["repo"]
                version = file_content.get("version", "")
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
        if version:
            sha = self.__determine_sha(owner, repo, version)
            deps_files = self.__get_python_deps_files(owner, repo, sha=sha)
        else:
            deps_files = self.__get_python_deps_files(owner, repo)
        build_systems: set[str] = set()
        if not deps_files:
            print("No pyproject.toml file found in the repository.")
            return False
        pyproject: dict[str, Any] = toml.loads(deps_files["pyproject.toml"])
        try:
            build_systems = set(pyproject["build-system"]["requires"])
        except KeyError:
            print("No build-system found in pyproject.toml file.")
            return False

        # Get deps from the Nix file
        try:
            if "build-system" in file_content and "list_content" in file_content["build-system"]:
                nix_file_deps = set(file_content["build-system"]["list_content"])
            else:
                nix_file_deps = set(file_content["build-system"])
        except KeyError:
            print("No build-system found in the Nix file.")
            nix_file_deps = set()

        # Compare
        if build_systems != nix_file_deps:
            diff = build_systems.symmetric_difference(nix_file_deps)
            print(
                "CAUTION: The build-system in the Nix file do not match the build-system found in the repository."
            )
            print(f"build-system in the repository: {build_systems}")
            print(f"build-system in the Nix file: {nix_file_deps}")
            print(f"Diff: {diff}")
            return False

        return True

    def __get_python_deps_files(self, owner: str, repo: str, sha: str = "") -> dict[str, str]:
        """Check if the repository has a pyproject.toml file."""
        github_service = GitHubService()
        deps_files = {"pyproject.toml"}
        files = {}
        with github_service.get_github_client() as g:
            try:
                repository = g.get_repo(f"{owner}/{repo}")
                for deps_file in deps_files:
                    try:
                        # Pass the SHA as the 'ref' argument so we get the file at that specific commit
                        kwargs = {"ref": sha} if sha else {}
                        content = repository.get_contents(deps_file, **kwargs)
                        
                        # PyGithub can return a list if the path is a directory, ensure it's a single file
                        if isinstance(content, list):
                            content = content[0]
                            
                        files[deps_file] = content.decoded_content.decode("utf-8")
                        print(f"Found {deps_file} in the repository (ref: {sha or 'default branch'}).")
                    except GithubException:
                        continue
            except GithubException:
                print("Repository not found or access denied.")
            except Exception as e:
                print(f"Error fetching repository contents: {e}")
            return files

    def __determine_sha(self, owner: str, repo: str, version: str) -> str:
        """Find the commit SHA for a given version, handling optional 'v' prefixes."""
        github_service = GitHubService()
        with github_service.get_github_client() as g:
            try:
                repository = g.get_repo(f"{owner}/{repo}")
                
                if version:
                    # Create a set of possible tag names to check against
                    target_tags = {version, f"v{version}"}
                    
                    # Iterate through the repository's tags
                    tags = repository.get_tags()
                    for tag in tags:
                        if tag.name in target_tags:
                            print(f"Matched tag '{tag.name}' to version '{version}'.")
                            return tag.commit.sha
                            
                    print(f"Warning: Could not find tag matching '{version}' or 'v{version}'. Falling back to default branch.")
                
                # Fallback: get the latest commit on the default branch if no version matches or is provided
                return repository.get_commits()[0].sha
                
            except GithubException:
                print("Repository not found or access denied.")
            except Exception as e:
                print(f"Error fetching repository contents: {e}")
            return ""
