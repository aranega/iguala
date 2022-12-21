from ast import parse, Module, ClassDef, Assign, arg, FunctionDef

from iguala import match

tree = parse(
    """
class A(object):
    Z = 0
    def __init__(self, x, y=3):
        self.x = x
        self.y = y
        self.z = 4

    class InnerCls(object):
        def __init__(self):
            self.inner_x = 1

class B(object):
    def __init__(self, w):
        if w > 0:
            self.w = w
        else:
            self. w = -1
"""
)


def test_match_all_cls():
    pattern = match(Module) % {"*": match(ClassDef) % {"name": "@name"}}

    result = pattern.match(tree)
    assert result.is_match is True
    assert len(result.bindings) == 3
    assert result.bindings[0]["name"] == "A"
    assert result.bindings[1]["name"] == "B"
    assert result.bindings[2]["name"] == "InnerCls"


def test_match_direct_cls():
    pattern = match(Module) % {"body": match(ClassDef)}

    result = pattern.match(tree)
    assert result.is_match is True
    assert len(result.contexts) == 2


def test_match_direct_cls_extract_name():
    pattern = match(Module) % {"body": match(ClassDef) % {"name": "@name"}}

    result = pattern.match(tree)
    assert result.is_match
    assert len(result.contexts) == 2


def test_match_instance_vars():
    pattern = match(Module) % {
        "*": match(ClassDef)
        % {
            "name": "@name",
            "body": match(FunctionDef)
            % {
                "name": "__init__",
                "body>*": match(Assign)
                % {
                    "targets>value>id": "self",
                    "targets>attr": "@attr",
                },
            },
        }
    }
    result = pattern.match(tree)
    assert result.is_match is True
    assert result.bindings == [
        {"name": "A", "attr": "x"},
        {"name": "A", "attr": "y"},
        {"name": "A", "attr": "z"},
        {"name": "B", "attr": "w"},
        {"name": "B", "attr": "w"},
        {"name": "InnerCls", "attr": "inner_x"},
    ]


def test_match_instances_same_args():
    pattern = match(Module) % {
        # that owns in all its children, recursively (i.e: somewhere, at any depth)
        # a ClassDef instance
        "*": match(ClassDef)
        % {
            "name": "@name",  # where name is equivalent to "name" (store the node)
            "body": match(FunctionDef)
            % {  # that has a FunctionDef in body
                "name": "__init__",  # that is named "__init__"
                "args>*": match(arg)
                % {
                    "*": "@attr"
                },  # among the args, there is one that a field equals to "attr"
                "body>*": match(Assign)
                % {  # and that has an Assign in it's body, somewhere (at any depth)
                    "targets>value>id": "self",  # where the target is "self"
                    "targets>attr": "@attr",  # where the attr is equivalent to "attr" (store the node)
                    "value>id": "@attr",  # and the "id" of the "value" of the assignment as is equivalent to "attr"
                },
            },
        }
    }
    result = pattern.match(tree)
    assert result.is_match is True
    assert result.bindings == [
        {"name": "A", "attr": "x"},
        {"name": "A", "attr": "y"},
        {"name": "B", "attr": "w"},
    ]
