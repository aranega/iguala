from iguala import is_not, match, as_matcher
from iguala.helpers import IdentitySet
from iguala.matchers import LiteralMatcher, NotMatcher, OrMatcher, SaveNodeMatcher

from .data_for_tests import ATest, InnerTest, obj_test, obj_test2


def test_builder():
    pattern = as_matcher(4)

    m1 = pattern | 5
    assert isinstance(m1, OrMatcher)

    assert isinstance(m1.left, LiteralMatcher)
    assert isinstance(m1.right, LiteralMatcher)

    m2 = 5 | pattern
    assert isinstance(m2, OrMatcher)

    assert isinstance(m2.left, LiteralMatcher)
    assert isinstance(m2.right, LiteralMatcher)


def test_simple_match():
    pattern = as_matcher(4) | 5

    assert pattern.match(4)
    assert pattern.match(5)

    assert not pattern.match(8)


def test_simple_match_object():
    pattern = match(ATest)[
        'x': as_matcher(4) | 5 | 6,
        'y': as_matcher(5) | 8
    ]


    pattern = match(ATest)[
        'x': as_matcher(9) | 5 | 6,
        'y': as_matcher(5) | 8
    ]
    assert not pattern.match(obj_test)

    pattern = match(ATest)[
        '*': match(InnerTest)[
            'name': as_matcher('foo.foo') | 'foo.foo.bar'
        ],
        '*': match(InnerTest)[
            'value': as_matcher(55) | 2
        ]
    ]
    assert pattern.match(obj_test)


    pattern = match(ATest)[
        '*': match(InnerTest)[
            'name': as_matcher('foo.foo') | 'foo.foo.bar',
            'value': as_matcher(55) | 1
        ],
    ]
    assert pattern.match(obj_test2)