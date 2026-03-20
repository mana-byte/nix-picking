from enum import Enum
from typing import Any

from nix_picking.parser.enums.builders import Builders
from nix_picking.review.review_points.models import ReviewPointBase
from nix_picking.review.review_points.python import python_points
from nix_picking.review.review_points.global_ import global_points


class Topics(Enum):
    GLOBAL = "Global"
    PYTHON = "Python"
    STANDARD_LIBRARY = "Standard Library"
    GO = "Go"
    RUST = "Rust"

    @classmethod
    def get_topic_from_builder(cls, builder: Builders) -> "Topics":
        mapping = {
            Builders.PYTHON_PACKAGE: cls.PYTHON,
            Builders.PYTHON_APP: cls.PYTHON,
            Builders.GO_MODULE: cls.GO,
            Builders.RUST_PACKAGE: cls.RUST,
            Builders.STANDARD: cls.STANDARD_LIBRARY,
            Builders.STANDARD_CC: cls.STANDARD_LIBRARY,
        }
        return mapping.get(builder, cls.GLOBAL)

    @classmethod
    def get_points_by_topic(cls, topic: "Topics") -> list[ReviewPointBase]:
        mapping = {
            cls.PYTHON: python_points(),
            cls.GLOBAL: global_points(),
        }
        return mapping.get(topic, [])
