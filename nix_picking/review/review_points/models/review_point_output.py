from dataclasses import dataclass
from typing import Any
import json

from nix_picking.review.review_points.enums.review_point_status import ReviewPointStatus


@dataclass
class ReviewPointOutput:
    review_point: str
    status: ReviewPointStatus
    stdrout: str
    output: list[str] | set[str] | dict[str, str] | None

    def to_dict(self) -> dict[str, Any]:
        output = self.output
        if isinstance(self.output, set):
            output = list(self.output)
        return {
            "review_point": self.review_point,
            "status": self.status,
            "stdout": self.stdrout,
            "output": output,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
