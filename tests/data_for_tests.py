from dataclasses import dataclass
from typing import List, Optional


@dataclass
class InnerTest(object):
    name: str
    value: int
    active: Optional[bool] = False
    children: Optional[List["InnerTest"]] = None


@dataclass
class ATest(object):
    x: int
    y: int
    name: str
    inner: InnerTest
    inner_list: List[InnerTest]


@dataclass
class BTest(ATest):
    z: int


obj_test = ATest(
    x=4,
    y=8,
    name="ATest name",
    inner=InnerTest(name="foo", value=3),
    inner_list=(
        InnerTest(
            name="foo",
            value=4,
            active=True,
            children=[
                InnerTest(
                    name="foo.foo",
                    value=8,
                    active=True,
                    children=[
                        InnerTest(
                            name="foo.foo.bar",
                            value=1,
                            children=[
                                InnerTest(name="foo.foo.bar.bar", value=1),
                                InnerTest(name="foo.foo.bar.baz", value=2, active=True),
                            ],
                        ),
                        InnerTest(name="foo.foo.baz", value=2),
                    ],
                )
            ],
        ),
        InnerTest(name="bar", value=3, active=True),
        InnerTest(name="foo", value=4),
    ),
)


dict_test = {
    "x": 4,
    "y": 8,
    "inner": {"name": "foo", "value": 3},
    "inner_list": [
        {
            "name": "foo",
            "value": 4,
            "active": True,
            "children": [
                {
                    "name": "foo.foo",
                    "value": 8,
                    "active": True,
                    "children": [
                        {
                            "name": "foo.foo.bar",
                            "value": 1,
                            "active": False,
                            "children": [
                                {
                                    "name": "foo.foo.bar.bar",
                                    "value": 1,
                                    "active": False,
                                },
                                {
                                    "name": "foo.foo.bar.baz",
                                    "value": 2,
                                    "active": True,
                                },
                            ],
                        },
                        {
                            "name": "foo.foo.baz",
                            "value": 2,
                            "active": True,
                        },
                    ],
                },
            ],
        },
        {
            "name": "bar",
            "value": 3,
            "active": True,
        },
        {
            "name": "foo",
            "value": 4,
            "active": False,
        },
    ],
}
