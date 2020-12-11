from types import SimpleNamespace

import pytest

from leval.excs import (
    InvalidOperation,
    NoSuchFunction,
    NoSuchValue,
    InvalidOperands,
    TooComplex,
)
from leval.simple import simple_eval

values = {
    "foo": 7,
    "bar": 8,
    "never": None,
    "muda": "muda",
    ("nep", "nop"): 10,
    "nup": SimpleNamespace(nap=9),
}
functions = {
    "abs": abs,
}

success_cases = [
    ("function calls", "abs(foo + 10) > 5", True),
    ("more complex expressions", "abs(foo + -bar) and bar == +8", True),
    ("set membership", "bar in {1, 2, 3, 8}", True),
    ("tuple membership", "bar not in (7, 6, 2)", True),
    ("concatenation", "'foo' 'bar'", "foobar"),
    ("AND logic", "foo and not bar", False),
    ("OR logic", "never or foo", True),
    ("attribute access via tuple names", "nep.nop + 10", 20),
    ("complex comparison", "(8, 3) >= (9, 2)", False),
    ("precedence (no parens here!)", "4 + 3 * 5 + 2", 21),
    ("precedence (with parens)", "4 + 3 * (5 + 2)", 25),
]

error_cases = [
    ("Can't index", "indx[9]", InvalidOperation),
    ("Can't call arbitrary functions", '__import__("sys")', NoSuchFunction),
    ("Invalid name", "njep + nop", NoSuchValue),
    ("Can't create long values", "'stack' * 10000", InvalidOperands),
    ("Plain old syntax error", "]", SyntaxError),
    (
        "Expression is too deeply nested",
        "(5+(5+(5+(5+(5*3)))))",
        TooComplex,
    ),
    ("Slicing is not allowed", "x[5::3]", InvalidOperation),
    ("Kwarg calls are not allowed", "abs(num=7)", InvalidOperation),
    ("Calls to non-names are not allowed", "8(num=7)", InvalidOperation),
    ("Complex calls are not allowed", "foo.bar(num=7)", InvalidOperation),
    ("Chained comparisons are not allowed", "5 < bar < 11", InvalidOperation),
    ("List comprehensions are not allowed", "[a for b in c]", InvalidOperation),
    ("Set comprehensions are not allowed", "{a for b in c}", InvalidOperation),
    ("Dict comprehensions are not allowed", "{a: a for b in c}", InvalidOperation),
    ("Formatting strings is not allowed", "f'foo'", InvalidOperation),
    ("Constructing dicts is not allowed", "{'d': 8}", InvalidOperation),
    ("Constructing lists is not allowed", "[1, 2, 3]", InvalidOperation),
    (
        "Attribute access via actual objects should fail for safety",
        "nup.nap + 10",
        NoSuchValue,
    ),
    ("Can't access weird methods off valid names", "abs.__class__", NoSuchValue),
    ("Arbitrary Python code is not allowed", "if x > a:\n    hello()", SyntaxError),
]


@pytest.mark.parametrize(
    "description, case, expected",
    success_cases,
    ids=[c[0] for c in success_cases],
)
def test_success(description, case, expected):
    assert simple_eval(case, values=values, functions=functions) == expected


@pytest.mark.parametrize(
    "description, case, expected",
    error_cases,
    ids=[c[0] for c in error_cases],
)
def test_error(description, case, expected):
    with pytest.raises(expected):
        simple_eval(case, values=values, functions=functions, max_depth=5)


@pytest.mark.parametrize(
    "kind, description, case, expected",
    (
        [("good",) + case for case in success_cases]
        + [
            ("bad",) + case
            for case in error_cases
            if case[-1] not in (InvalidOperands, NoSuchValue, NoSuchFunction)
        ]
    ),
)
def test_verify(kind, description, case, expected):
    fn = lambda: simple_eval(
        case, values=values, functions=functions, max_depth=6, verify_only=True
    )
    if kind == "bad":
        with pytest.raises(expected):
            fn()
    else:
        assert fn()
