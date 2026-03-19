import sys, inspect
from nix_picking.review.review_points.base import ReviewPointBase

from .check_hash_github import CheckHashGitHub

# Declare all the review points in this module for easy import elsewhere
__all__ = ["CheckHashGitHub"]

def global_points() -> list[ReviewPointBase]:
    points: list[ReviewPointBase] = []
    for _, obj in inspect.getmembers(sys.modules[__name__]):
        if (
            inspect.isclass(obj)
            and issubclass(obj, ReviewPointBase)
            and obj is not ReviewPointBase
        ):
            points.append(obj())
    return points
