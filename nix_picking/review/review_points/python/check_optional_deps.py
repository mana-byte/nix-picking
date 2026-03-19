import re
import toml
from typing import final, override, Any

from nix_picking.review.review_points.base import ReviewPointBase
from nix_picking.review.services.github import GitHubService
from nix_picking.review.review_points.utils import GitHubRepoUtils


@final
class CheckOptionalDeps(ReviewPointBase):
    @override
    def __init__(self):
        super().__init__()
        self._importance = 5
        self._explanation = "Check if the Nix optional dependencies match the repository's pyproject.toml."
        self._source = (
            "https://nixos.org/manual/nixpkgs/stable/#buildpythonpackage-function"
        )

    @override
    def apply(self, file_content: dict[str, Any]) -> bool:
        # 1. Identify Repo
        owner, repo, version = GitHubRepoUtils.extract_repo_info(file_content)
        if not (owner and repo):
            return False

        # 2. Fetch Remote Data
        repo_deps: set[str] = set()
        github_service = GitHubService()
        
        with github_service.get_github_client() as g:
            try:
                repository = g.get_repo(f"{owner}/{repo}")
                sha = GitHubRepoUtils.determine_sha(repository, version)
                
                # Check pyproject.toml
                pyproject_str = GitHubRepoUtils.get_file_content(repository, "pyproject.toml", sha)
                if pyproject_str:
                    repo_deps.update(self._parse_pyproject_deps(pyproject_str))
                    
            except Exception as e:
                print(f"GitHub Error: {e}")
                return False

        if not repo_deps:
            print("No pyproject.toml found in the repository, or no optional dependencies found in it.")
            return False

        # 3. Get deps from the Nix file
        nix_file_deps = self._extract_nix_deps(file_content)
        if not nix_file_deps:
            print("No dependencies found in the Nix file.")
            return False

        # 4. Compare
        diff = GitHubRepoUtils.fuzzy_diff(repo_deps, nix_file_deps)
        if diff:
            print("WARNING: optional dependencies in the Nix file do not match the repository.")
            print(f"Repository: {repo_deps}")
            print(f"Nix file: {nix_file_deps}")
            print(f"Diff: {diff}")
            return False

        return True

    def _parse_pyproject_deps(self, content: str) -> set[str]:
        """Parses [project.dependencies] from pyproject.toml."""
        try:
            data = toml.loads(content)
            deps_group_list = data.get("project", {}).get("optional-dependencies", {})
            opt_deps = set()
            for group_name, group_deps in deps_group_list.items():
                if group_name == "all":
                    continue
                if isinstance(group_deps, list):
                    opt_deps.update({re.split(r'[>=<~!,;]', dep.lower())[0].strip() for dep in group_deps})
            return opt_deps
        except Exception as e:
            return set()

    def _extract_nix_deps(self, file_content: dict[str, Any]) -> set[str]:
        """Safely extract Nix dependencies based on dictionary structure."""
        deps = file_content.get("optional-dependencies", {})
        output_opt_deps = set()
        if isinstance(deps, dict) and "list_content" in deps:
            for group_name, group_deps in deps["list_content"].items():
                if isinstance(group_deps, list):
                    output_opt_deps.update(set(group_deps))
        else:
            for group_name, group_deps in deps.items():
                if isinstance(group_deps, list):
                    output_opt_deps.update(set(group_deps))
        return output_opt_deps
        
