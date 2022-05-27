import time
from types import SimpleNamespace

import pytest

from leval.evaluator import Evaluator
from leval.excs import (
    InvalidOperands,
    InvalidOperation,
    NoSuchFunction,
    NoSuchValue,
    Timeout,
    TooComplex,
)
from leval.simple import simple_eval
from leval.universe.default import EvaluationUniverse
from leval.universe.weakly_typed import WeaklyTypedSimpleUniverse

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
    ("Formatting strings is not allowed", "f'foo'", (SyntaxError, InvalidOperation)),
    ("Constructing dicts is not allowed", "{'d': 8}", InvalidOperation),
    ("Constructing lists is not allowed", "[1, 2, 3]", InvalidOperation),
    (
        "Attribute access via actual objects should fail for safety",
        "nup.nap + 10",
        NoSuchValue,
    ),
    ("Can't access weird methods off valid names", "abs.__class__", NoSuchValue),
    ("Arbitrary Python code is not allowed", "if x > a:\n    hello()", SyntaxError),
    ("Can't access attributes off constants", "(3).__class__", InvalidOperation),
    (
        "Walruses aren't allowed",
        "(a := 3) + 8",
        (SyntaxError, InvalidOperation),  # Error depends on Python version
    ),
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
    fn = lambda: simple_eval(  # noqa: E731
        case, values=values, functions=functions, max_depth=6, verify_only=True
    )
    if kind == "bad":
        with pytest.raises(expected):
            fn()
    else:
        assert fn()


def test_weak_typing():
    def weak_eval(s):
        uni = WeaklyTypedSimpleUniverse(values={"s": "8", "f": 8}, functions={})
        return Evaluator(uni).evaluate_expression(s)

    assert weak_eval("s + s + s") == "888"
    assert weak_eval("s + s + s + 10") == 898
    assert weak_eval("s + f") == 16
    assert weak_eval("f + s") == 16
    with pytest.raises(InvalidOperands):
        weak_eval("s * 8")
    with pytest.raises(InvalidOperands):
        weak_eval("8 * s")


def test_time_limit():
    def slow(x=None):
        time.sleep(0.2)
        return x or 1

    with pytest.raises(Timeout):
        simple_eval(
            "min(slow(3), slow(.1)) + slow(.5)",
            functions={
                "slow": slow,
                "min": min,
            },
            max_time=0.3,
        )


def test_allowed_container_types():
    # Disallow all container types:
    evaluator = Evaluator(EvaluationUniverse(), allowed_container_types=[])
    for expr in ("[1, 2, 3]", "{1, 2, 3}", "(1, 2, 3)"):
        with pytest.raises(InvalidOperation):
            evaluator.evaluate_expression(expr)


def test_complex():
    evaluator = Evaluator(EvaluationUniverse(), allowed_constant_types=(int, complex))
    assert evaluator.evaluate_expression("(6 + 3j) / 3") == 2 + 1j


def test_readme_example():
    assert simple_eval("1 + 2") == 3
    assert simple_eval("x < -80 or x > 125 or x == 85", values={"x": 85})
    assert simple_eval("abs(x) > 80", values={"x": -85}, functions={"abs": abs})
    assert simple_eval("x.y.z + 8", values={("x", "y", "z"): 34}) == 42
