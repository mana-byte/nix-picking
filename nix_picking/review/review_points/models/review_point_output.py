from dataclasses import dataclass
from typing import Any
import json


@dataclass
class ReviewPointOutput:
    review_point: str
    passed: bool
    stdrout: str
    output: list[str] | set[str] | dict[str, str] | None

    def to_dict(self) -> dict[str, Any]:
        output = self.output
        if isinstance(self.output, set):
            output = list(self.output)
        return {
            "review_point": self.review_point,
            "passed": self.passed,
            "stdout": self.stdrout,
            "output": output,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
