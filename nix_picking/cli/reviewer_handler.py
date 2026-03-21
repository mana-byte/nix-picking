from nix_picking.review.reviewer import Reviewer
from typing import Any, final


@final
class ReviewHandler:
    def __init__(self, pr: int | None = None, fork: str | None = None):
        self.reviewer = Reviewer(pr=pr, fork=fork)

    def review(
        self, withGlobal: bool = True, additional_parse_levels: int = 1
    ) -> dict[str, Any]:
        return self.reviewer.review(
            withGlobal=withGlobal, additional_parse_levels=additional_parse_levels
        )

    def review_file(
        self,
        raw_nix_file: str,
        additional_parse_levels: int = 1,
        withGlobal: bool = True,
    ) -> dict[str, Any]:
        return self.reviewer.review_file(
            raw_nix_file=raw_nix_file,
            additional_parse_levels=additional_parse_levels,
            withGlobal=withGlobal,
        )
