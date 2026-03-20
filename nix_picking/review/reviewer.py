from collections import defaultdict
from typing import Any, final

from nix_picking.parser import NixParser
from nix_picking.parser.enums.builders import Builders
from nix_picking.review.review_points.enums import Topics
from nix_picking.review.review_points.utils import GitHubRepoUtils


@final
class Reviewer:

    BLACK_LISTED_FILES = {
        "pkgs/top-level/python-packages.nix",
        "maintainers/maintainer-list.nix",
        "pkgs/by-name/hy/hyprland/info.json",
    }

    def __init__(self, pr: int | None, fork: str | None = None):
        self.pr = pr
        self.owner: str | None = "NixOS"
        self.repo: str | None = "nixpkgs"
        if fork:
            self.owner, self.repo = fork.split("/") if "/" in fork else (None, None)
            if not self.owner or not self.repo:
                raise ValueError(f"Invalid fork format: {fork}")

    def _go_through_files(
        self,
        files: dict[str, str],
        withGlobal: bool = True,
        additional_parse_levels: int = 1,
    ) -> None:
        parser = NixParser()
        parsed_files: dict[str, Any] = defaultdict()
        for filename, content in files.items():
            print(f"Reviewing file: {filename}")
            try:
                parsed_files[filename] = parser.parse(
                    content, additional_levels=additional_parse_levels
                )
                builder = Builders.get_builder_from_file(content)
                if not builder:
                    print(f"Could not determine builder for {filename}, skipping.")
                    continue
                topic = Topics.get_topic_from_builder(builder)
                points = Topics.get_points_by_topic(topic)
                if withGlobal:
                    global_points = Topics.get_points_by_topic(Topics.GLOBAL)
                    points.extend(global_points)
                for point in points:
                    print(f"\n {point.name}: ")
                    if point.apply(parsed_files[filename]):
                        print("PASSED")
                    print("\n")

            except ValueError:
                print(f"Failed to parse {filename}, skipping.")
                continue

    def review(self, withGlobal: bool = True, additional_parse_levels: int = 1) -> None:
        if not self.pr:
            print(
                "No PR number provided, skipping review. If you want to review a local file use review_file() instead."
            )
            return
        files = GitHubRepoUtils.fetch_pull_request_files(
            pr_number=self.pr,
            repo_full_name=f"{self.owner}/{self.repo}",
            black_listed_files=self.BLACK_LISTED_FILES,
        )
        self._go_through_files(
            files,
            withGlobal=withGlobal,
            additional_parse_levels=additional_parse_levels,
        )

    def review_file(
        self,
        raw_nix_file: str,
        additional_parse_levels: int = 1,
        withGlobal: bool = True,
    ) -> None:
        file = {"local_file.nix": raw_nix_file}
        self._go_through_files(
            file, withGlobal=withGlobal, additional_parse_levels=additional_parse_levels
        )


if __name__ == "__main__":
    reviewer = Reviewer(pr=500483)
    with open("tests/inputs/python/a2a-sdk/default.nix") as f:
        file = f.read()
    reviewer.review_file(file)
    # reviewer.review()
