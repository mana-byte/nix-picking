from typing import Any

from nix_picking.review.review_points.enums.review_point_status import ReviewPointStatus

from .review_point_output import ReviewPointOutput


class ReviewPointBase:
    def __init__(self):
        self._name: str = self.__class__.__name__
        self._importance: int | None = None
        self._explanation: str | None = None
        self._source: str | None = "No source"
        self.output: ReviewPointOutput = ReviewPointOutput(
            review_point=self.name,
            status=ReviewPointStatus.FAILED,
            stdrout="",
            output=[],
        )
        _ = self.apply({})

    def apply(self, file_content: dict[str, Any]) -> ReviewPointOutput:
        """Apply the review point to the given file. Return True if the review point is applicable, False otherwise."""
        raise NotImplementedError("Subclasses must implement the apply method")

    def to_stdrout(self, input_str: str) -> None:
        self.output.stdrout += input_str

    def fail(
        self,
        output: list[str] | set[str] | dict[str, str] | None = None,
        message: str = "",
    ) -> ReviewPointOutput:
        self.output.status = ReviewPointStatus.FAILED
        self.output.output = output
        self.to_stdrout(message)
        return self.output

    def skip(
        self,
        output: list[str] | set[str] | dict[str, str] | None = None,
        message: str = "",
    ) -> ReviewPointOutput:
        self.output.status = ReviewPointStatus.SKIPPED
        self.output.output = output
        self.to_stdrout(message)
        return self.output

    def pass_(
        self,
        output: list[str] | set[str] | dict[str, str] | None = None,
        message: str = "",
    ) -> ReviewPointOutput:
        self.output.status = ReviewPointStatus.PASSED
        self.output.output = output
        self.to_stdrout(message)
        return self.output

    @property
    def name(self) -> str:
        if not self._name:
            raise ValueError("Name cannot be empty")
        return self._name

    @property
    def importance(self) -> int:
        if self._importance is None:
            raise ValueError("Importance cannot be None")
        if not (1 <= self._importance <= 5):
            raise ValueError("Importance must be between 1 and 10")
        return self._importance

    @property
    def explanation(self) -> str:
        if not self._explanation:
            raise ValueError("Explanation cannot be empty")
        return self._explanation

    @property
    def source(self) -> str:
        if not self._source:
            raise ValueError("Source cannot be empty")
        return self._source

    @classmethod
    def inheritors(cls, include_self: bool = False) -> "set[ReviewPointBase]":
        """
        Returns a set of all subclasses of this class.
        Args:
            include_self: If True, includes the class itself in the result.
                          Defaults to False.
        Returns:
            set[type]: A set of all subclasses (and optionally the class itself).
        """
        subclasses = set()
        if include_self:
            subclasses.add(cls)
        work = list(cls.__subclasses__())
        while work:
            parent = work.pop()
            if parent not in subclasses:
                subclasses.add(parent)
                work.extend(parent.__subclasses__())
        return subclasses
