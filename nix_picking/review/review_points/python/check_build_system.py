import re
import toml
from typing import final, override, Any

from nix_picking.review.review_points.base import ReviewPointBase
from nix_picking.review.repositories import GitHubRepoUtils

@final
class CheckBuildSystem(ReviewPointBase):
    @override
    def __init__(self):
        super().__init__()
        self._importance = 5
        self._explanation = "Check build-system in pyproject.toml"
        self._source = "https://nixos.org/manual/nixpkgs/stable/#buildpythonpackage-function"

    @override
    def apply(self, file_content: dict[str, Any]) -> bool:
        # 1. Identity Repo
        owner, repo, version = GitHubRepoUtils.extract_repo_info(file_content)
        if not (owner and repo):
            return False

        # 2. Fetch Remote Data
        try:
            repository = f"{owner}/{repo}"
            sha = GitHubRepoUtils.determine_sha(repository, version)
            toml_text = GitHubRepoUtils.get_file_content(repository, "pyproject.toml", sha)
        except Exception as e:
            print(f"GitHub Error: {e}")
            return False

        if not toml_text:
            print("No pyproject.toml found in the repository, or no build-system found.")
            return False

        # 3. Process Build Systems
        repo_build_systems = self._parse_pyproject_build_system(toml_text)
        nix_build_systems = self._get_nix_build_systems(file_content)

        # 4. Compare
        diff = GitHubRepoUtils.fuzzy_diff(repo_build_systems, nix_build_systems)
        if diff:
            print(f"Mismatch found in build-system requirements. Diff: {diff}")
            return False

        return True

    def _parse_pyproject_build_system(self, content: str) -> set[str]:
        """Parses pyproject.toml and strips version constraints."""
        try:
            data = toml.loads(content)
            requires = data.get("build-system", {}).get("requires", [])
            # Convert 'setuptools >= 61.0' -> 'setuptools'
            return {re.split(r'[>=<~!,;]', req.lower())[0].strip() for req in requires}
        except Exception:
            return set()

    def _get_nix_build_systems(self, file_content: dict[str, Any]) -> set[str]:
        """Extracts build-system list from parsed Nix file content."""
        bs = file_content.get("build-system", {})
        if isinstance(bs, str):
            return {bs}
        if isinstance(bs, dict) and "list_content" in bs:
            return set(bs["list_content"])
        return set(bs) if isinstance(bs, list) else set()
