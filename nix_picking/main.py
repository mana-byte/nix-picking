
if __name__ == "__main__":
    from nix_picking.review.review_points.models import ReviewPointBase

    def inheritors(klass):
        subclasses = set()
        work = [klass]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses:
                    subclasses.add(child)
                    work.append(child)
        return subclasses

    print(inheritors(ReviewPointBase))
