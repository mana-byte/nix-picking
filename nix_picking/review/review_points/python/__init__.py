import sys, inspect

from nix_picking.review.review_points.base import ReviewPointBase

from .check_deps import CheckDeps
from .check_build_system import CheckBuildSystem
from .check_optional_deps import CheckOptionalDeps

# Declare all the review points in this module for easy import elsewhere
__all__ = ["CheckDeps", "CheckBuildSystem", "CheckOptionalDeps"]

def python_points() -> list[ReviewPointBase]:
    points: list[ReviewPointBase] = []
    for _, obj in inspect.getmembers(sys.modules[__name__]):
        if (
            inspect.isclass(obj)
            and issubclass(obj, ReviewPointBase)
            and obj is not ReviewPointBase
        ):
            points.append(obj())
    return points
