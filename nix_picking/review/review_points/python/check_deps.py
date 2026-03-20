import re
import toml
from typing import final, override, Any

from nix_picking.review.review_points.models import ReviewPointBase
from nix_picking.review.repositories import GitHubRepoUtils
from nix_picking.review.review_points.models.review_point_output import (
    ReviewPointOutput,
)


@final
class CheckDeps(ReviewPointBase):
    @override
    def __init__(self):
        super().__init__()
        self._importance = 5
        self._explanation = "Check if the Nix dependencies match the repository's pyproject.toml or requirements.txt."
        self._source = (
            "https://nixos.org/manual/nixpkgs/stable/#buildpythonpackage-function"
        )

    @override
    def apply(self, file_content: dict[str, Any]) -> ReviewPointOutput:
        # 1. Identify Repo
        owner, repo, version = GitHubRepoUtils.extract_repo_info(file_content)
        if not (owner and repo):
            return self.fail()

        # 2. Fetch Remote Data
        repo_deps: set[str] = set()

        repository = f"{owner}/{repo}"
        sha = GitHubRepoUtils.determine_sha(repository, version)

        # Check pyproject.toml
        pyproject_str = GitHubRepoUtils.get_file_content(
            repository, "pyproject.toml", sha
        )
        if pyproject_str:
            repo_deps.update(self._parse_pyproject_deps(pyproject_str))

        # Check requirements.txt (if it exists, merge them)
        reqs_str = GitHubRepoUtils.get_file_content(repository, "requirements.txt", sha)
        if reqs_str:
            repo_deps.update(self._parse_requirements_txt(reqs_str))

        if not repo_deps:
            self.to_stdrout(
                "No dependencies found in the repository's pyproject.toml or requirements.txt."
            )
            return self.fail()

        # 3. Get deps from the Nix file
        nix_file_deps = self._extract_nix_deps(file_content)
        if not nix_file_deps:
            self.to_stdrout("Could not extract dependencies from the Nix file.")
            return self.fail()

        # 4. Compare
        diff = GitHubRepoUtils.fuzzy_diff(repo_deps, nix_file_deps)
        if diff:
            self.to_stdrout("Dependency mismatch \n")
            self.to_stdrout(f"Repo dependencies: {repo_deps} \n")
            self.to_stdrout(f"Nix file dependencies: {nix_file_deps} \n")
            return self.fail(diff)

        return self.pass_()

    def _parse_pyproject_deps(self, content: str) -> set[str]:
        """Parses [project.dependencies] from pyproject.toml."""
        try:
            data = toml.loads(content)
            deps_list: list[str] = data.get("project", {}).get("dependencies", [])
            return {re.split(r"[>=<~!,;]", d.lower())[0].strip() for d in deps_list}
        except Exception:
            return set()

    def _parse_requirements_txt(self, content: str) -> set[str]:
        """Parses requirements.txt, stripping versions and comments."""
        deps: set[str] = set()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-r"):
                continue
            # Strip version specifiers and comments on the same line
            clean_name = re.split(r"[>=<~!,; #]", line.lower())[0].strip()
            if clean_name:
                deps.add(clean_name)
        return deps

    def _extract_nix_deps(self, file_content: dict[str, Any]) -> set[str]:
        """Safely extract Nix dependencies based on dictionary structure."""
        deps = file_content.get("dependencies", {})
        if isinstance(deps, str):
            return {deps}
        if isinstance(deps, dict) and "list_content" in deps:
            return set(deps["list_content"])
        return set(deps) if isinstance(deps, list) else set()
