from typing import Any, final, override
import json
import subprocess

from nix_picking.review.review_points.models import ReviewPointBase
from nix_picking.review.repositories import GitHubRepoUtils


@final
class CheckHashGitHub(ReviewPointBase):

    @override
    def __init__(self):
        super().__init__()
        self._importance = 5
        self._explanation = (
            "Check if the hash in the fetchFromGitHub function is correct"
        )
        self._source = "https://nixos.org/manual/nixpkgs/stable/#fetchfromgithub"

    @override
    def apply(self, file_content: dict[str, Any]) -> bool:
        owner, repo, ver = GitHubRepoUtils.extract_repo_info(file_content)
        if not (owner and repo and ver):
            return False

        hash = file_content.get("src", {}).get("hash", "")
        if not hash:
            print("No hash found in the fetchFromGitHub function.")
            return False

        tag = GitHubRepoUtils.get_tag_from_version(f"{owner}/{repo}", ver)
        if not tag:
            print(f"Could not find a matching tag for version '{ver}' in the repository.")
            return False

        expected_hash = self._get_nix_git_hash(f"{owner}/{repo}", tag)

        if expected_hash != hash:
            print(f"WARNING: Hash mismatch for {owner}/{repo} at tag '{tag}':")
            print(f"  Expected: {expected_hash}")
            print(f"  Found:    {hash}")
            return False

        return True

    def _get_nix_git_hash(self, repo: str, rev: str) -> str:
        repo_url = f"https://github.com/{repo}"
        try:
            result = subprocess.run(
                ["nix-prefetch-git", repo_url, "--rev", rev, "--quiet"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error fetching git hash: {e.stderr}")
            return ""
        nix_data: dict[str, str | bool] = json.loads(result.stdout)
        return str(nix_data["hash"])
