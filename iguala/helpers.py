from collections.abc import MutableSet
from itertools import chain


class match(object):
    def __init__(self, cls):
        from .matchers import ObjectMatcher

        self.matcher = ObjectMatcher(cls)
        self.matcher.properties = {}

    def __mod__(self, properties):
        self.matcher.properties = properties
        return self.matcher

    def __matmul__(self, alias):
        from .matchers import SaveNodeMatcher

        return SaveNodeMatcher(alias, self.matcher)

    def __invert__(self):
        self.matcher.subclassmatch = True
        return self

    @property
    def and_subclasses(self):
        return ~self

    def such_as(self, properties):
        return self % properties

    def as_matcher(self):
        return self.matcher


def is_not(matcher):
    from .matchers import NotMatcher, as_matcher

    if isinstance(matcher, NotMatcher):
        return matcher.matcher
    return NotMatcher(as_matcher(matcher))


class IdentitySet(MutableSet):
    def __init__(self, iterable=()):
        self.map = {}
        self |= iterable

    def __len__(self):
        return len(self.map)

    def __iter__(self):
        return iter(self.map.values())

    def __contains__(self, x):
        return id(x) in self.map

    def add(self, value):
        self.map[id(value)] = value

    def discard(self, value):
        self.map.pop(id(value), None)

    def __repr__(self):
        return f"{self.__class__.__name__}({list(self)})"


def flat(iterable, iterable_cls=(list, set, tuple)):
    if not isinstance(iterable, iterable_cls):
        return [iterable]
    try:
        result = []
        remainder = iter(iterable)
        while True:
            first = next(remainder)
            if isinstance(first, iterable_cls):
                remainder = chain(first, remainder)
            else:
                result.append(first)
    except StopIteration:
        return result
