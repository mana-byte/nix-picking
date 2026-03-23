import pytest

import os
import json
from nix_picking.parser import NixParser
from nix_picking.review.review_points.enums.topics import Topics
from nix_picking.review.review_points.models import ReviewPointBase
from tests.test_review_points import (
    REVIEW_POINT_EXPECTED_OUTPUTS_DIR,
    REVIEW_POINT_LANGUAGE_REFERENCES_DIR,
)


ALL_TOPICS = {topic for topic in Topics}

ALL_REVIEW_POINT_CLASSES = {
    review_point_class
    for topic in ALL_TOPICS
    for review_point_class in Topics.get_point_classes_by_topic(topic)
}


@pytest.mark.parametrize("review_point_class", ALL_REVIEW_POINT_CLASSES)
def test_review_point_attribute_and_method_implementation(
    review_point_class: ReviewPointBase,
):
    print(f"Testing {review_point_class.name}")
    review_point = review_point_class.create()
    # Check that the review point has the required attributes
    _ = review_point.importance
    _ = review_point.explanation
    _ = review_point.source
    # Check implementation of apply, fail, skip, pass_ methods
    _ = review_point.apply({})
    _ = review_point.fail()
    _ = review_point.skip()
    _ = review_point.pass_()


class BaseTestReviewPoint:
    """
    Base class for testing review points against language-specific Nix files.
    Subclasses must define 'language' and parameterize 'review_point_class'.
    """

    language: str = ""

    @pytest.fixture(autouse=True)
    def setup_parser(self):
        self.parser = NixParser()

    def test_apply_review_point_against_nix_file(
        self, review_point_class: ReviewPointBase
    ):
        review_point = review_point_class.create()
        language_ref_dir = os.path.join(
            REVIEW_POINT_LANGUAGE_REFERENCES_DIR, self.language
        )
        language_expected_dir = os.path.join(
            REVIEW_POINT_EXPECTED_OUTPUTS_DIR, self.language, review_point.name
        )

        if not os.path.isdir(language_ref_dir):
            pytest.skip(f"Reference directory not found for language: {self.language}")

        for filename in os.listdir(language_ref_dir):
            if not filename.endswith(".nix"):
                continue

            # Get output to test
            nix_path = os.path.join(language_ref_dir, filename)
            with open(nix_path, "r") as f:
                file_content = self.parser.parse(f.read())

            # Get expected output
            expected_path = os.path.join(
                language_expected_dir,
                filename.replace(".nix", ".json"),
            )

            try:
                with open(expected_path, "r") as f:
                    expected_output = json.load(f)

                assert isinstance(
                    expected_output, dict
                ), "Expected output should be a dictionary"

            except (FileNotFoundError, json.JSONDecodeError, AssertionError) as e:
                pytest.skip(
                    f"Skipping {review_point.name} on {filename}. Reason: {type(e).__name__}"
                )

            # Apply review point and compare with expected output
            result = review_point.apply(file_content).to_dict()
            result["status"] = result["status"].value  # Convert enum to str
            del result["stdout"]

            assert (
                result == expected_output
            ), f"Failed for {review_point.name} on {filename}"


# Language test

PYTHON_REVIEW_POINT_CLASSES = [
    review_point_class
    for review_point_class in Topics.get_point_classes_by_topic(Topics.PYTHON)
]


@pytest.mark.parametrize("review_point_class", PYTHON_REVIEW_POINT_CLASSES)
class TestPythonReviewPoints(BaseTestReviewPoint):
    language = "python"
