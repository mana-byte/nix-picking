from typing import Any

from nix_picking.review.review_points.base import ReviewPointBase
import sys, inspect

__all__ = []

def global_points() -> list[ReviewPointBase]:
    points: list[ReviewPointBase] = []
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if (
            inspect.isclass(obj)
            and issubclass(obj, ReviewPointBase)
            and obj is not ReviewPointBase
        ):
            points.append(obj())
    return points
