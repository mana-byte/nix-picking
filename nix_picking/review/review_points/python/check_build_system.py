import re
import toml
from typing import final, override, Any

from nix_picking.review.review_points.models import ReviewPointBase
from nix_picking.review.repositories import GitHubRepoUtils
from nix_picking.review.review_points.models.review_point_output import ReviewPointOutput

@final
class CheckBuildSystem(ReviewPointBase):
    @override
    def __init__(self):
        super().__init__()
        self._importance = 5
        self._explanation = "Check build-system in pyproject.toml"
        self._source = "https://nixos.org/manual/nixpkgs/stable/#buildpythonpackage-function"

    @override
    def apply(self, file_content: dict[str, Any]) -> ReviewPointOutput:
        # 1. Identity Repo
        owner, repo, version = GitHubRepoUtils.extract_repo_info(file_content)
        if not (owner and repo):
            return self.fail()

        # 2. Fetch Remote Data
        repository = f"{owner}/{repo}"
        sha = GitHubRepoUtils.determine_sha(repository, version)
        toml_text = GitHubRepoUtils.get_file_content(repository, "pyproject.toml", sha)

        if not toml_text:
            self.to_stdrout("No pyproject.toml found in the repository, or no build-system found.")
            return self.fail()

        # 3. Process Build Systems
        repo_build_systems = self._parse_pyproject_build_system(toml_text)
        nix_build_systems = self._get_nix_build_systems(file_content)

        # 4. Compare
        diff = GitHubRepoUtils.fuzzy_diff(repo_build_systems, nix_build_systems)
        if diff:
            self.to_stdrout("Build-system mismatch \n")
            self.to_stdrout(f"Repo build-system: {repo_build_systems} \n")
            self.to_stdrout(f"Nix file build-system: {nix_build_systems}")
            return self.fail(diff)

        return self.pass_()

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
