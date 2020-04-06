import pytest

from leval.excs import (
    InvalidOperation,
    NoSuchFunction,
    NoSuchValue,
    InvalidOperands,
    TooComplex,
)
from leval.simple import simple_eval

values = {"foo": 7, "bar": 8, "muda": "muda", ("nep", "nop"): 10}
functions = {"abs": abs}


@pytest.mark.parametrize(
    "case, expected",
    [
        ("abs(foo + 10) > 5", True),
        ("abs(foo + -bar) and bar == 8", True),
        ("bar in {1, 2, 3, 8}", True),
        ("'foo' 'bar'", "foobar"),
        ("foo and not bar", False),
        ("nep.nop + 10", 20),
        ("(8, 3) >= (9, 2)", False),
    ],
)
def test_success(case, expected):
    assert simple_eval(case, values=values, functions=functions) == expected


@pytest.mark.parametrize(
    "case, expected",
    [
        ("indx[9]", InvalidOperation),
        ('__import__("sys")', NoSuchFunction),
        ("njep + nop", NoSuchValue),
        ("'stack' * 10000", InvalidOperands),
        ("]", SyntaxError),
        ("(5+(5+(5+(5+(5+(5+(5+(5+(5+(5+10))))))))))", TooComplex),
        ("x[5::3]", InvalidOperation),
        ("[a for b in c]", InvalidOperation),
        ("f'foo'", InvalidOperation),
    ],
)
def test_error(case, expected):
    with pytest.raises(expected):
        simple_eval(case, values=values, functions=functions, max_depth=5)
