from enum import Enum

from nix_picking.parser.enums.builders import Builders
from nix_picking.review.review_points.models import ReviewPointBase
from nix_picking.review.review_points.models.languages import *

# The language modules need to be imported here to ensure the language is registered
import nix_picking.review.review_points.languages.global_
import nix_picking.review.review_points.languages.python
import nix_picking.review.review_points.languages.go
import nix_picking.review.review_points.languages.rust


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
    def get_point_classes_by_topic(cls, topic: "Topics") -> set[ReviewPointBase]:
        """
        Maps each language topic to its corresponding review point classes.
        """
        mapping = {
            cls.PYTHON: PythonReviewPoint.inheritors(),
            cls.GLOBAL: GlobalReviewPoint.inheritors(),
            cls.GO: GoReviewPoint.inheritors(),
            cls.RUST: RustReviewPoint.inheritors(),
        }
        return mapping.get(topic, set())
