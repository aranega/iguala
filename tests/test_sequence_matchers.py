from dataclasses import dataclass
import pytest

from iguala import as_matcher, is_not, match


class A(object):
    ...


a = A()


@pytest.mark.parametrize(
    "pattern, data, expected",
    [
        ([], [], True),
        ([1], [1], True),
        ([1, 2], [1], False),
        (["a", 2], ["a", 2], True),
        (["a", 2], ["a", 2], True),
        ([], (), True),
        ([1], (1,), True),
        ([1, 3], (1, 3), True),
        ([1, 3, 3], (1, 3), False),
        ([1, 3, 3], (3, 3, 1), False),
        ([match(A), match(A)], [a, a], True),
        ([match(A), match(A)], [A(), A()], True),
    ],
)
def test_simple_list(pattern, data, expected):
    matcher = as_matcher(pattern)
    result = matcher.match(data)
    assert result.is_match is expected


@pytest.mark.parametrize(
    "pattern, data, expected, variables",
    [
        (["@x"], [1], True, {"x": 1}),
        (["@x", "@x"], [1, 1], True, {"x": 1}),
        (["@x", "@y"], [1, 2], True, {"x": 1, "y": 2}),
        (["@x", "@y"], [1, 1], True, {"x": 1, "y": 1}),
        (["@x", "@y", "@x"], [1, 3, 1], True, {"x": 1, "y": 3}),
        ([..., "@x"], [1, 3, 1], True, {"x": 1}),
        ([..., "@y", "@x"], [1, 3, 1], True, {"x": 1, "y": 3}),
        (["@y", ..., "@x"], [4, 3, 1], True, {"x": 1, "y": 4}),
        (["@x", ..., "@x"], [1, 3, 1], True, {"x": 1}),
        (["@x", ..., "@x"], [1, 3, 4, 1], True, {"x": 1}),
        (["@x", ..., "@x"], [1, 3, 3], False, {}),
        (["@x", "@x"], [2, 3], False, {}),
        (["@x", is_not("@x")], [2, 3], True, {"x": 2}),
        (is_not(["@x", is_not("@x")]), [2, 3], False, {}),
        (is_not(["@x", is_not("@x")]), [2, 2], True, {}),
        (is_not(["@x", "@x"]), [2, 2], False, {}),
        (is_not(["@x", "@x"]), [2, 3], True, {}),
    ],
)
def test_simple_list_with_wildcard(pattern, data, expected, variables):
    matcher = as_matcher(pattern)
    result = matcher.match(data)
    assert result.is_match is expected

    for bindings in result.bindings:
        for var, val in variables.items():
            assert bindings[var] == val


@pytest.mark.parametrize(
    "pattern, data, expected, variables",
    [
        (["@x", ...], [1], True, ({"x": 1},)),
        (["@x", ...], [1, 2, 3], True, ({"x": 1},)),
        ([..., "@x", ...], [1, 2, 3], True, ({"x": 1}, {"x": 2}, {"x": 3})),
        ([..., "@x", ..., "@x"], [1, 2, 3, 2], True, ({"x": 2},)),
        ([..., "@x", ..., "@x"], [1, 2, 3, 2, 2], True, ({"x": 2}, {"x": 2})),
        ([..., "@x", ..., "@y"], [1, 2, 3], True, ({"x": 1, "y": 3}, {"x": 2, "y": 3})),
        # (["@x", ...], [1], True, {"x": 1}),
        # (["@x", "@x"], [1, 1], True, {"x": 1}),
        # (["@x", "@y"], [1, 2], True, {"x": 1, "y": 2}),
        # (["@x", "@y"], [1, 1], True, {"x": 1, "y": 1}),
        # (["@x", "@y", "@x"], [1, 3, 1], True, {"x": 1, "y": 3}),
        # ([..., "@x"], [1, 3, 1], True, {"x": 1}),
        # ([..., "@y", "@x"], [1, 3, 1], True, {"x": 1, "y": 3}),
        # (["@y", ..., "@x"], [4, 3, 1], True, {"x": 1, "y": 4}),
        # (["@x", ..., "@x"], [1, 3, 1], True, {"x": 1}),
        # (["@x", ..., "@x"], [1, 3, 4, 1], True, {"x": 1}),
        # (["@x", ..., "@x"], [1, 3, 3], False, {}),
        # (["@x", "@x"], [2, 3], False, {}),
        # (["@x", is_not("@x")], [2, 3], True, {"x": 2}),
        # (is_not(["@x", is_not("@x")]), [2, 3], False, {}),
        # (is_not(["@x", is_not("@x")]), [2, 2], True, {}),
        # (is_not(["@x", "@x"]), [2, 2], False, {}),
        # (is_not(["@x", "@x"]), [2, 3], True, {}),
    ],
)
def test_ellipsis_list(pattern, data, expected, variables):
    matcher = as_matcher(pattern)
    result = matcher.match(data)
    assert result.is_match is expected
    assert len(result.bindings) == len(variables)

    for ctx, bindings in zip(variables, result.bindings):
        for var, val in ctx.items():
            assert bindings[var] == val


def test_sequence_matcher_generator():
    @dataclass
    class A:
        x: int
        y: int | str
        tab: list[int | str]

    def i_element_after(i, x, var):
        return as_matcher([..., x, *["@_"]*i, f"@{var}", ...])

    p = match(A)[
        "x": "@step",
        "y": "@y",
        "tab": lambda step, y: i_element_after(step, y, "res")
    ]

    a = A(x=2, y="r", tab=[3, 4, "r", 3, 3, 5, 6, "r", 1, 2, 8])

    res = p.match(a)["res"]

    assert len(res) == 2
    assert res == [5, 8]


def test_matcher_generator_iterate_list():
    @dataclass
    class A:
        x: int
        tab: list[int | str]

    a = A(x=3, tab=[3, 4, "r", 3, 3, 5, 6, "r", 1, 2, 8])

    p = match(A)[
        "x": "@x",
        "tab": lambda x: x
    ]

    res = p.match(a)["x"]

    assert len(res) == 3



def test_matcher_generator_save_nodes():
    @dataclass
    class A:
        x: int
        tab: list[int | str]

    a = A(x=3, tab=[3, 4, "r", 3, 3, 5, 6, "r", 1, 2, 8])

    p = match(A)[
        "x": "@x",
        "tab": as_matcher(lambda x: x) @ "xx"
    ]

    res = p.match(a)

    assert len(res["x"]) == 3
    assert len(res["xx"]) == 3
    assert res["xx"] == [3, 3, 3]


# def test_matcher_generator_inner_save_nodes():
#     @dataclass
#     class A:
#         x: int
#         tab: list[int | str]

#     a = A(x=3, tab=[3, 4, "r", 3, 3, 5, 6, "r", 1, 2, 8])

#     p = match(A)[
#         "x": "@x",
#         "tab": as_matcher(lambda x: as_matcher(lambda z: z) @ "z") @ "xx"
#     ]

#     res = p.match(a)

#     assert len(res["x"]) == 3
#     assert len(res["xx"]) == 3
#     assert res["xx"] == [3, 3, 3]