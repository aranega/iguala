import pytest
from iguala import as_matcher, match
import sys

from .data_for_tests import ATest, BTest, InnerTest, obj_test


def test_lambda_matcher():
    pattern = match(obj_test.__class__)[
        "x":"@x",
        "y" : as_matcher(lambda x: x * 2) @ "y",
    ]

    result = pattern.match(obj_test)
    assert result.is_match

    bindings = result.contexts[0]
    assert len(bindings) == 2
    assert bindings["x"] == 4
    assert bindings["y"] == 8

    for z in bindings:
        assert z in ("x", "y")

    del bindings["x"]
    assert len(bindings) == 1
    assert "x" not in bindings
    assert bindings["y"] == 8


def test_lambda_matcher2():
    pattern = match(obj_test.__class__) % {
        "x": "@x",
        "y": as_matcher(lambda x: x * 2) @ "y",
    }

    result = pattern.match(obj_test)
    assert result.is_match

    bindings = result.contexts[0]
    assert len(bindings) == 2
    assert bindings["x"] == 4
    assert bindings["y"] == 8

    for z in bindings:
        assert z in ("x", "y")

    del bindings["x"]
    assert len(bindings) == 1
    assert "x" not in bindings
    assert bindings["y"] == 8


def test_lambda_matcher_uncomplete():
    pattern = match(obj_test.__class__)["x":4, "y" : as_matcher(lambda x: x * 8)]

    result = pattern.match(obj_test)
    assert result.is_match

    bindings = result.bindings[0]
    assert "x" not in bindings

    print(result)
    assert bool(result) is True


def test_lambda_matcher_uncomplete():
    pattern = match(obj_test.__class__) % {"x": 4, "y": as_matcher(lambda x: x * 8)}

    result = pattern.match(obj_test)
    assert result.is_match

    bindings = result.bindings[0]
    assert "x" not in bindings

    print(result)
    assert bool(result) is True


def test_lambda_matcher_desorder():
    pattern = match(obj_test.__class__)[
        "y" : as_matcher(lambda x: x * 2) @ "y",
        "x":"@x",
    ]

    result = pattern.match(obj_test)
    assert result.is_match

    bindings = result.bindings[0]
    assert bindings["x"] == 4
    assert bindings["y"] == 8


def test_lambda_matcher_desorder2():
    pattern = match(obj_test.__class__) % {
        "y": as_matcher(lambda x: x * 2) @ "y",
        "x": "@x",
    }

    result = pattern.match(obj_test)
    assert result.is_match

    bindings = result.bindings[0]
    assert bindings["x"] == 4
    assert bindings["y"] == 8


def test_lambda_matcher_desorder3():
    pattern = match(obj_test.__class__)[
        "y" : as_matcher(lambda x: x * 5) @ "y",
        "x":"@x",
    ]

    result = pattern.match(obj_test)
    assert result.is_match is False


def test_lambda_matcher_desorder4():
    pattern = match(obj_test.__class__) % {
        "y": as_matcher(lambda x: x * 5) @ "y",
        "x": "@x",
    }

    result = pattern.match(obj_test)
    assert result.is_match is False


def test_results_binding_access():
    pattern = (~match(object))[
        "y": as_matcher(lambda x: x * 2) @ "y",
        "x": "@x",
    ]
    result = pattern.match(obj_test)
    assert result.is_match is True

    assert result["x"] == [4]
    assert result["y"] == [8]

    assert result["x"::set] == {4}


def test_match_multiple_types():
    pattern = match(ATest) % {}
    assert pattern.match(BTest(0, 0, 'foo', InnerTest('bar', 5), [], 5)).is_match is False

    pattern = match(ATest, BTest) % {}
    assert pattern.match(BTest(0, 0, 'foo', InnerTest('bar', 5), [], 5)).is_match is True


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Union notation is not available for Python < 3.10")
def test_match_union_type():
    pattern = match(ATest) % {}
    assert pattern.match(BTest(0, 0, 'foo', InnerTest('bar', 5), [], 5)).is_match is False

    pattern = match(ATest | BTest) % {}
    assert pattern.match(BTest(0, 0, 'foo', InnerTest('bar', 5), [], 5)).is_match is True
