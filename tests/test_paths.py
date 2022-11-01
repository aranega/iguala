import pytest

from iguala import match
from iguala.paths import (
    ChildrenRecursivePath,
    ComposedPath,
    DictPath,
    DirectPath,
    NamedRecursivePath,
    as_path,
)

from .data_for_tests import dict_test, obj_test


def test_as_path_direct_dict_composed():
    path = as_path("x")
    assert isinstance(path, DirectPath)

    path = as_path("x", dictkey=True)
    assert isinstance(path, DictPath)

    path = as_path("x>y>z")
    assert isinstance(path, ComposedPath)
    assert isinstance(path.paths[0], DirectPath)
    assert path.paths[0].path == "x"
    assert isinstance(path.paths[1], DirectPath)
    assert path.paths[1].path == "y"
    assert isinstance(path.paths[2], DirectPath)
    assert path.paths[2].path == "z"

    path = as_path("x>y>z", dictkey=True)
    assert isinstance(path, ComposedPath)
    assert isinstance(path.paths[0], DictPath)
    assert path.paths[0].path == "x"
    assert isinstance(path.paths[1], DictPath)
    assert path.paths[1].path == "y"
    assert isinstance(path.paths[2], DictPath)
    assert path.paths[2].path == "z"


def test_as_path_recursive():
    path = as_path("x*")
    assert isinstance(path, NamedRecursivePath)
    assert isinstance(path.path, DirectPath)
    assert path.path.path == "x"

    path = as_path("x*", dictkey=True)
    assert isinstance(path, NamedRecursivePath)
    assert isinstance(path.path, DictPath)
    assert path.path.path == "x"

    path = as_path("*")
    assert isinstance(path, ChildrenRecursivePath)

    path = as_path("*", dictkey=True)
    assert isinstance(path, ChildrenRecursivePath)


def test_as_path_composed():
    path = as_path("x>y*")
    assert isinstance(path, ComposedPath)
    assert isinstance(path.paths[0], DirectPath)
    assert path.paths[0].path == "x"
    assert isinstance(path.paths[1], NamedRecursivePath)
    assert isinstance(path.paths[1].path, DirectPath)
    assert path.paths[1].path.path == "y"

    path = as_path("x*>y")
    assert isinstance(path, ComposedPath)
    assert isinstance(path.paths[0], NamedRecursivePath)
    assert isinstance(path.paths[0].path, DirectPath)
    assert path.paths[0].path.path == "x"
    assert isinstance(path.paths[1], DirectPath)
    assert path.paths[1].path == "y"


def test_itself():
    path = as_path("x>y*")
    matcher = match(ComposedPath) % {
        "paths": [
            match(DirectPath) % {"path": "x"},
            match(NamedRecursivePath) % {"path": match(DirectPath) % {"path": "y"}},
        ]
    }
    result = matcher.match(path)
    assert result.is_match

    path = as_path("x*>y*")
    matcher = match(ComposedPath) % {
        "paths": [
            match(NamedRecursivePath) % {"path": match(DirectPath) % {"path": "x"}},
            match(NamedRecursivePath) % {"path": match(DirectPath) % {"path": "y"}},
        ]
    }
    result = matcher.match(path)
    assert result.is_match

    path = as_path("x+")
    matcher = match(ComposedPath) % {
        "paths": [
            match(DirectPath) % {"path": "x"},
            match(NamedRecursivePath) % {"path": match(DirectPath) % {"path": "x"}},
        ]
    }
    result = matcher.match(path)
    assert result.is_match


@pytest.mark.parametrize(
    "path, data, expected",
    [
        ("x", None, []),
        ("x", 3, []),
        ("x", "foo", []),
        ("x", True, []),
        ("x", False, []),
        ("ww", dict_test, []),
        ("x", dict_test, [4]),
        ("inner", dict_test, [{"name": "foo", "value": 3}]),
    ],
)
def test_direct_dict_path(path, data, expected):
    p = DictPath(path)
    assert p.resolve_from(data) == expected


@pytest.mark.parametrize(
    "path, data, expected",
    [
        ("x", None, []),
        ("x", 3, []),
        ("x", "foo", []),
        ("x", True, []),
        ("x", False, []),
        ("ww", obj_test, []),
        ("x", obj_test, [4]),
        ("y", obj_test, [8]),
        ("name", obj_test, ["ATest name"]),
        ("inner", obj_test, [obj_test.inner]),
        ("inner_list", obj_test, list(obj_test.inner_list)),
    ],
)
def test_direct_obj_path(path, data, expected):
    p = DirectPath(path)
    assert p.resolve_from(data) == expected


@pytest.mark.parametrize(
    "paths, data, expected",
    [
        (("x", "x"), None, []),
        (("x", "x"), 3, []),
        (("x", "x"), "foo", []),
        (("x", "x"), True, []),
        (("x", "x"), False, []),
        (("inner", "ww"), dict_test, []),
        (("inner", "name"), dict_test, ["foo"]),
        (("inner", "value"), dict_test, [3]),
        (("inner_list", "name"), dict_test, ["foo", "bar", "foo"]),
        (("inner_list", "active"), dict_test, [True, True, False]),
    ],
)
def test_composed_dict_path(paths, data, expected):
    p = ComposedPath([DictPath(x) for x in paths])
    assert p.resolve_from(data) == expected


@pytest.mark.parametrize(
    "paths, data, expected",
    [
        (("x", "x"), None, []),
        (("x", "x"), 3, []),
        (("x", "x"), "foo", []),
        (("x", "x"), True, []),
        (("x", "x"), False, []),
        (("inner", "ww"), obj_test, []),
        (("inner", "name"), obj_test, ["foo"]),
        (("inner", "value"), obj_test, [3]),
        (("inner_list", "name"), obj_test, ["foo", "bar", "foo"]),
        (("inner_list", "active"), obj_test, [True, True, False]),
    ],
)
def test_composed_obj_path(paths, data, expected):
    p = ComposedPath([DirectPath(x) for x in paths])
    assert p.resolve_from(data) == expected


@pytest.mark.parametrize(
    "path, data, expected",
    [
        ("*>x", None, []),
        ("*>x", 3, []),
        ("*>x", "foo", []),
        ("*>x", True, []),
        ("*>x", False, []),
        ("*>ww", dict_test, []),
        (
            "*>name",
            dict_test,
            [
                "foo",
                "foo",
                "bar",
                "foo",
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
        ("*>value", dict_test, [3, 4, 3, 4, 8, 1, 2, 1, 2]),
        (
            "inner_list>*>name",
            dict_test,
            [
                "foo",
                "bar",
                "foo",
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
        (
            "inner_list>children>*>name",
            dict_test,
            [
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
        # (
        #     "inner_list>children>*>children>*>name",
        #     dict_test,
        #     [
        #         "foo.foo.bar",
        #         "foo.foo.baz",
        #         "foo.foo.bar.bar",
        #         "foo.foo.bar.baz",
        #     ],
        # ),
    ],
)
def test_composed_dict_path_rec(path, data, expected):
    p = as_path(path, dictkey=True)
    res = p.resolve_from(data)
    assert len(res) == len(expected)
    assert res == expected


@pytest.mark.parametrize(
    "path, data, expected",
    [
        ("*>x", None, []),
        ("*>x", 3, []),
        ("*>x", "foo", []),
        ("*>x", True, []),
        ("*>x", False, []),
        ("*>ww", obj_test, []),
        (
            "*>name",
            obj_test,
            [
                "ATest name",
                "foo",
                "foo",
                "bar",
                "foo",
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
        ("*>value", obj_test, [3, 4, 3, 4, 8, 1, 2, 1, 2]),
        (
            "inner_list>*>name",
            obj_test,
            [
                "foo",
                "bar",
                "foo",
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
        (
            "inner_list>children>*>name",
            obj_test,
            [
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
    ],
)
def test_composed_obj_path_rec(path, data, expected):
    p = as_path(path)
    res = p.resolve_from(data)
    assert len(res) == len(expected)
    assert res == expected


@pytest.mark.parametrize(
    "path, data, expected",
    [
        ("x*>x", None, []),
        ("x*>x", 3, []),
        ("x*>x", "foo", []),
        ("x*>x", True, []),
        ("x*>x", False, []),
        ("x*>ww", obj_test, []),
        (
            "inner_list>children*>name",
            obj_test,
            [
                "foo",
                "bar",
                "foo",
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
        (
            "inner_list>children>children*>name",
            obj_test,
            [
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
        (
            "inner_list>children+>name",
            obj_test,
            [
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
    ],
)
def test_composed_obj_path_rec_named(path, data, expected):
    p = as_path(path)
    res = p.resolve_from(data)
    assert len(res) == len(expected)
    assert res == expected


@pytest.mark.parametrize(
    "path, data, expected",
    [
        ("x*>x", None, []),
        ("x*>x", 3, []),
        ("x*>x", "foo", []),
        ("x*>x", True, []),
        ("x*>x", False, []),
        ("x*>ww", dict_test, []),
        (
            "inner_list>children*>name",
            dict_test,
            [
                "foo",
                "bar",
                "foo",
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
        (
            "inner_list>children>children*>name",
            dict_test,
            [
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
        (
            "inner_list>children+>name",
            dict_test,
            [
                "foo.foo",
                "foo.foo.bar",
                "foo.foo.baz",
                "foo.foo.bar.bar",
                "foo.foo.bar.baz",
            ],
        ),
    ],
)
def test_composed_dict_path_rec_named(path, data, expected):
    p = as_path(path, dictkey=True)
    res = p.resolve_from(data)
    assert len(res) == len(expected)
    assert res == expected
