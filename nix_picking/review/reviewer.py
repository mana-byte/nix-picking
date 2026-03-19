from collections import defaultdict
from typing import Any, final

from nix_picking.parser import NixParser
from nix_picking.parser.enums.builders import Builders
from nix_picking.review.services.github import GitHubService
from nix_picking.review.review_points.enums import Topics


@final
class Reviewer:
    def __init__(self, pr: int | None, fork: str | None = None):
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
        if not self.pr:
            print(
                "No PR number provided, skipping review. If you want to review a local file use review_file() instead."
            )
            return
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

    def review_file(self, raw_nix_file: str, additional_parse_levels: int = 1) -> None:
        parser = NixParser()
        file = {"local_file.nix": raw_nix_file}
        parsed_file: dict[str, Any] = defaultdict()
        for filename, content in file.items():
            print(f"Reviewing file: {filename}")
            try:
                parsed_file["local_file.nix"] = parser.parse(
                    raw_nix_file, additional_levels=additional_parse_levels
                )
                print(parsed_file)
                builder = Builders.get_builder_from_file(content)
                if not builder:
                    print(f"Could not determine builder for {filename}, skipping.")
                    continue
                topic = Topics.get_topic_from_builder(builder)
                for point in Topics.get_points_by_topic(topic):
                    print(f"\n {point.name}: ")
                    if point.apply(parsed_file[filename]):
                        print("PASSED")
                    print("\n")

            except ValueError:
                print(f"Failed to parse {filename}, skipping.")
                continue


if __name__ == "__main__":
    reviewer = Reviewer(pr=500483)
    with open("tests/inputs/python/a2a-sdk/default.nix") as f:
        file = f.read()
    reviewer.review_file(file)

    # reviewer.review()
