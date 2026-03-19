import urllib.parse
from typing import Any
from github.Repository import Repository
from github import GithubException
import textdistance


class GitHubRepoUtils:
    @staticmethod
    def extract_repo_info(file_content: dict[str, Any]) -> tuple[str, str, str]:
        """Extracts (owner, repo, version) from Nix file content."""
        src = file_content.get("src", {})
        version = file_content.get("version", "")

        if src.get("function") == "fetchFromGitHub":
            return src.get("owner", ""), src.get("repo", ""), version

        homepage = file_content.get("meta", {}).get("homepage", "")
        if "github.com" in homepage:
            path = urllib.parse.urlparse(homepage).path
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 2:
                return parts[0], parts[1], version

        return "", "", ""

    @staticmethod
    def determine_sha(repository: Repository, version: str) -> str:
        """Finds the commit SHA for a version/tag, handling 'v' prefix."""
        if not version:
            return repository.get_commits()[0].sha

        target_tags = {version, f"v{version}"}
        try:
            for tag in repository.get_tags():
                if tag.name in target_tags:
                    return tag.commit.sha
        except GithubException:
            pass

        return repository.get_commits()[0].sha

    @staticmethod
    def get_file_content(repository: Repository, path: str, sha: str = "") -> str:
        """Fetches raw text content of a file at a specific SHA."""
        try:
            kwargs = {"ref": sha} if sha else {}
            content = repository.get_contents(path, **kwargs)
            if isinstance(content, list):
                content = content[0]
            return content.decoded_content.decode("utf-8")
        except (GithubException, UnicodeDecodeError):
            return ""

    @staticmethod
    def fuzzy_diff(nix_deps: set[str], py_deps: set[str], threshold: float = 0.8) -> set[str]:
        """
        Returns a symmetric difference, but ignores items that are 'close enough'.
        """
        matched_nix = set()
        matched_py = set()

        for n_dep in nix_deps:
            for p_dep in py_deps:
                # 1. Direct match or "extra" match (markitdown[pdf] contains markitdown)
                if n_dep == p_dep or n_dep in p_dep or p_dep in n_dep:
                    matched_nix.add(n_dep)
                    matched_py.add(p_dep)
                    continue
                
                # 2. Fuzzy match for typos or naming conventions (python-magic vs magic)
                similarity = textdistance.levenshtein.normalized_similarity(n_dep, p_dep)
                if similarity >= threshold:
                    matched_nix.add(n_dep)
                    matched_py.add(p_dep)

        # Return items that didn't find a partner in the other set
        unmatched_nix = nix_deps - matched_nix
        unmatched_py = py_deps - matched_py
        
        return unmatched_nix.union(unmatched_py)
