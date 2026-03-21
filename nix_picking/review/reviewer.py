from collections import defaultdict
from typing import Any, final

from nix_picking.parser import NixParser
from nix_picking.parser.enums.builders import Builders
from nix_picking.review.review_points.enums import Topics
from nix_picking.review.repositories import GitHubRepoUtils
from nix_picking.review.review_points.models import ReviewPointBase


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
        self.report = defaultdict(list)

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
                point_classes = Topics.get_point_classes_by_topic(topic)
                if withGlobal:
                    global_point_classes = Topics.get_point_classes_by_topic(
                        Topics.GLOBAL
                    )
                    point_classes.update(global_point_classes)
                for ReviewPointClass in point_classes:
                    point = ReviewPointClass.create()
                    report = point.apply(parsed_files.get(filename, {}))
                    self.report[filename].append(report.to_dict())

            except ValueError:
                print(f"Failed to parse {filename}, skipping.")
                continue

    def review(
        self, withGlobal: bool = True, additional_parse_levels: int = 1
    ) -> dict[str, Any]:
        if not self.pr:
            print(
                "No PR number provided, skipping review. If you want to review a local file use review_file() instead."
            )
            return {}
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
        return self.report

    def review_file(
        self,
        raw_nix_file: str,
        additional_parse_levels: int = 1,
        withGlobal: bool = True,
    ) -> dict[str, Any]:
        file = {"local_file.nix": raw_nix_file}
        self._go_through_files(
            file, withGlobal=withGlobal, additional_parse_levels=additional_parse_levels
        )
        return self.report


if __name__ == "__main__":
    # Source - https://stackoverflow.com/a/5883218
    # Posted by Duncan, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-03-20, License - CC BY-SA 3.0

    def inheritors(klass):
        subclasses = set()
        work = [klass]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses:
                    subclasses.add(child)
                    work.append(child)
        return subclasses

    print(inheritors(ReviewPointBase))
