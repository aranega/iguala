from iguala import is_not, match
from iguala.helpers import IdentitySet
from iguala.matchers import LiteralMatcher, NotMatcher, SaveNodeMatcher

from .data_for_tests import ATest


def test_builder():
    pattern = match(ATest)

    assert isinstance(pattern @ "x", SaveNodeMatcher)

    assert (~pattern).matcher.subclassmatch is True
    assert pattern.and_subclasses.matcher.subclassmatch is True

    pattern.such_as({"x": 3})
    k, v = list(pattern.matcher.properties)[0]
    assert k.path == "x"
    assert isinstance(v, LiteralMatcher)


def test_isnot():
    pattern = is_not(3)

    assert isinstance(pattern, NotMatcher)
    assert isinstance(pattern.matcher, LiteralMatcher)


def test_isnot_simplification():
    p = is_not(3)

    assert isinstance(is_not(is_not(is_not(p))), LiteralMatcher)
    assert isinstance(is_not(is_not(p)), NotMatcher)


def test_identity_set():
    x, y = object(), object()

    s = IdentitySet()

    s.add(x)
    s.add(y)
    s.add(x)

    assert len(s) == 2
    assert x in s
    assert y in s

    for z in s:
        assert z in s

    assert repr(s) is not None
    assert repr(s) != ""

    s.discard(x)

    assert len(s) == 1
    assert x not in s
    assert y in s
