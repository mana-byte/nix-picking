from collections import defaultdict
from typing import Any, final

from nix_picking.parser import NixParser
from nix_picking.parser.enums.builders import Builders
from nix_picking.review.review_points.base import ReviewPointBase
from nix_picking.review.services.github import GitHubService
from nix_picking.review.review_points.enums import Topics


@final
class Reviewer:
    def __init__(self, pr: int, fork: str | None = None):
        self.pr = pr
        self.owner: str | None = "NixOS"
        self.repo: str | None = "nixpkgs"
        self.github_service = GitHubService()
        if fork:
            self.owner, self.repo = fork.split("/") if "/" in fork else (None, None)
            if not self.owner or not self.repo:
                raise ValueError(f"Invalid fork format: {fork}")

        self.files: dict[str, str] | None = None
        self.parsed_files: dict[str, Any] = defaultdict(str)


    def review(self) -> None:
        parser = NixParser()
        self.files = self.github_service.fetch_pull_request_files(
            pr_number=self.pr, repo_full_name=f"{self.owner}/{self.repo}"
        )
        for filename, content in self.files.items():
            print(f"Reviewing file: {filename}")
            try:
                self.parsed_files[filename] = parser.parse(content)
                builder = Builders.get_builder_from_file(content)
                if not builder:
                    print(f"Could not determine builder for {filename}, skipping.")
                    continue
                topic = Topics.get_topic_from_builder(builder)
                for point in Topics.get_points_by_topic(topic):
                    print(f"\n {point.name}: ")
                    if point.apply(self.parsed_files[filename]):
                        print("PASSED")
                print("\n")

            except ValueError:
                print(f"Failed to parse {filename}, skipping.")
                continue

if __name__ == "__main__":
    reviewer = Reviewer(pr=501295)
    reviewer.review()

