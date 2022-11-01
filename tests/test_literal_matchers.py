import pytest

from iguala import as_matcher


@pytest.mark.parametrize(
    "pattern, data, expected",
    [
        (3, 3, True),
        (3, 4, False),
        (3, 3.0, True),
        (3, "r", False),
        (3, True, False),
        (3, False, False),
        (3, None, False),
    ],
)
def test_integer_matcher(pattern, data, expected):
    matcher = as_matcher(pattern)
    result = matcher.match(data)
    assert result.is_match is expected


@pytest.mark.parametrize(
    "pattern, data, expected",
    [
        ("foo", "foo", True),
        ("foo", "Foo", False),
        ("foo", 3, False),
        ("foo", 3.0, False),
        ("foo", True, False),
        ("foo", False, False),
        ("True", True, False),
        ("False", False, False),
        ("foo", None, False),
    ],
)
def test_string_matcher(pattern, data, expected):
    matcher = as_matcher(pattern)
    result = matcher.match(data)
    assert result.is_match is expected


@pytest.mark.parametrize(
    "pattern, data, expected",
    [
        (None, None, True),
        (None, "Foo", False),
        (None, 3, False),
        (None, 3.0, False),
        (None, True, False),
        (None, False, False),
    ],
)
def test_None_matcher(pattern, data, expected):
    matcher = as_matcher(pattern)
    result = matcher.match(data)
    assert result.is_match is expected


@pytest.mark.parametrize(
    "pattern, data, expected",
    [
        (True, True, True),
        (True, False, False),
        (False, False, True),
        (False, True, False),
        (True, "True", False),
        (False, "False", False),
        (False, 0, False),
        (True, 0, False),
        (True, None, False),
        (False, None, False),
    ],
)
def test_bool_matcher(pattern, data, expected):
    matcher = as_matcher(pattern)
    result = matcher.match(data)
    assert result.is_match is expected
