"""
Module to declare language support for review points.
All review points related to X language should be declared in the coresponding module and inherit from X language class
"""

from . import ReviewPointBase


class GlobalReviewPoint(ReviewPointBase):
    pass


class PythonReviewPoint(ReviewPointBase):
    pass


class GoReviewPoint(ReviewPointBase):
    pass

class RustReviewPoint(ReviewPointBase):
    pass
