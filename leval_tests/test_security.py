"""
Security-focused tests: sandbox escape and resource-exhaustion scenarios.

The first group asserts that a broad variety of code-execution / introspection
escapes are refused.  The second group covers resource-exhaustion behaviour:
sequence-multiplication amplification is blocked, while the remaining bounds
(cooperative ``max_time``, structural-only ``verify()``, unwrapped native
exceptions) are documented so their behaviour stays visible.
"""

import time
from types import SimpleNamespace

import pytest

from leval.evaluator import Evaluator
from leval.excs import EvaluatorError, InvalidOperands
from leval.extras.common_boolean_evaluator import CommonBooleanEvaluator
from leval.simple import simple_eval
from leval.universe.weakly_typed import WeaklyTypedSimpleUniverse


class _Marker:
    """A rich host object in the values dict; nothing on it should be reachable."""

    secret = "TOP_SECRET"

    def __init__(self):
        self.data = "instance_secret"

    def owned(self):  # pragma: no cover - must never be called by the sandbox
        raise AssertionError("sandbox escaped: method was called")


SEC_VALUES = {
    "foo": 7,
    "bar": 8,
    "obj": _Marker(),
    "ns": SimpleNamespace(secret="nested"),
    ("a", "b"): 5,
}
SEC_FUNCTIONS = {"abs": abs, "min": min, "max": max}


# Expressions that MUST NOT execute host code or reach forbidden objects.
# We only require that *some* exception is raised (the exact type varies by
# Python version and by which guard fires first).
ESCAPE_ATTEMPTS = [
    # Classic introspection chains.
    "().__class__.__bases__[0].__subclasses__()",
    "(1).__class__",
    "'x'.__class__",
    "(1).__class__.__mro__",
    # Attribute access on host objects must not become getattr().
    "obj.secret",
    "obj.data",
    "obj.owned",
    "obj.owned()",
    "ns.secret",
    # Dunder access on whitelisted callables/names.
    "abs.__globals__",
    "abs.__class__",
    "abs.__self__",
    "min.__self__.__class__",
    "abs.__call__(1)",
    # Attribute access on the result of a call / group / literal.
    "abs(1).__class__",
    "(foo).__class__",
    "().__class__",
    "(1,).__class__",
    "'a'.join(['b'])",
    "[].append(1)",
    "{}.update",
    # Calling things that are not whitelisted bare-name functions.
    "__import__('os')",
    "__import__('os').system('id')",
    "eval('1')",
    "exec('x=1')",
    "getattr(abs, '__globals__')",
    "type(1)",
    "open('/etc/passwd')",
    "globals()",
    "locals()",
    "vars()",
    "compile('1', '', 'eval')",
    "(lambda: 1)()",
    # Comprehensions / generators.
    "[x for x in (1, 2)]",
    "{x for x in (1, 2)}",
    "{x: x for x in (1, 2)}",
    "(x for x in (1, 2))",
    # Subscript / slice.
    "foo[0]",
    "foo[0:1]",
    "'abcd'[0]",
    "(1, 2, 3)[0]",
    # Starred / kwargs / f-strings / walrus.
    "min(*(1, 2))",
    "abs(x=1)",
    "f'{abs}'",
    "f'{obj.secret}'",
    "(z := 1)",
    # Exotic operators that could enable big-number / bit tricks.
    "~5",
    "5 ** 2",
    "5 % 2",
    "5 << 2",
    "5 | 2",
    "5 & 2",
    "5 @ 2",
]


@pytest.mark.parametrize("expr", ESCAPE_ATTEMPTS)
def test_escape_blocked_strict(expr):
    """No escape attempt should succeed in the strict simple_eval universe."""
    with pytest.raises(Exception) as exc_info:
        simple_eval(expr, values=SEC_VALUES, functions=SEC_FUNCTIONS, max_depth=15)
    # Must not be an AssertionError from a host method actually running.
    assert not isinstance(exc_info.value, AssertionError)


@pytest.mark.parametrize("expr", ESCAPE_ATTEMPTS)
def test_escape_blocked_common(expr):
    """The same attempts are refused by the weakly-typed CommonBooleanEvaluator."""
    with pytest.raises(Exception) as exc_info:
        CommonBooleanEvaluator().evaluate(expr, {"foo": 7, "bar": 8})
    assert not isinstance(exc_info.value, AssertionError)


def test_host_object_attributes_are_never_getattr():
    """Attribute access resolves via the values dict, never getattr on the object."""
    # A dotted name that is *not* a registered tuple key is simply unknown.
    with pytest.raises(EvaluatorError):
        simple_eval("obj.secret", values=SEC_VALUES)
    # A registered dotted (tuple) key does resolve - by dict lookup, not attribute walk.
    assert simple_eval("a.b + 1", values=SEC_VALUES) == 6


# --------------------------------------------------------------------------
# Resource exhaustion
# --------------------------------------------------------------------------


def test_strict_universe_blocks_sequence_multiplication():
    """The strict universe refuses tuple*int (numbers-only), so no amplification."""
    with pytest.raises(InvalidOperands):
        simple_eval("(1,) * 1000000")


def test_weakly_typed_sequence_mul_is_blocked():
    """
    Weakly-typed universes must refuse ``sequence * int`` amplification.

    ``guard_numbers_only_mul`` allows multiplication only between numbers, so a
    tuple literal multiplied by a large integer -- which would otherwise allocate
    a proportionally huge tuple in a single, non-preemptible operation -- is
    rejected instead of executed.
    """
    uni = WeaklyTypedSimpleUniverse(values={}, functions={})
    with pytest.raises(InvalidOperands):
        Evaluator(uni).evaluate_expression("(1,) * 1000000000")
    # ...while multiplying numbers still works.
    assert Evaluator(uni).evaluate_expression("6 * 7") == 42
    # CommonBooleanEvaluator is likewise protected.
    with pytest.raises(InvalidOperands):
        CommonBooleanEvaluator().evaluate("(1,) * 1000000000", {})


def test_verify_is_structural_only():
    """
    Show verify() blesses an expression that raises at evaluate() time.

    verify() uses the no-op VerifierUniverse, which does not perform the actual
    operations, so it is a syntactic / structural check only -- not a guarantee
    that evaluate() will succeed or stay within resource limits.
    """
    assert CommonBooleanEvaluator().verify("1 / 0") is True
    with pytest.raises(ZeroDivisionError):
        CommonBooleanEvaluator().evaluate("1 / 0", {})


def test_max_time_is_not_preemptive_within_one_operation():
    """
    Show max_time cannot interrupt work done inside a single node visit.

    max_time is only checked at node-visit boundaries, so a single slow function
    call (or any single expensive operation) runs to completion regardless of the
    limit. Here a function that sleeps well past the budget still returns its
    value -- max_time is a coarse, cooperative bound, not a hard timeout.
    """

    def slow():
        time.sleep(0.05)
        return 123

    result = simple_eval(
        "slow()",
        functions={"slow": slow},
        max_time=0.0001,
        max_depth=5,
    )
    assert result == 123


@pytest.mark.parametrize(
    "expr",
    [
        "1 / 0",  # ZeroDivisionError
        "min()",  # TypeError from the builtin
    ],
)
def test_native_exceptions_are_not_wrapped(expr):
    """
    Show operator/function errors propagate as native types, not EvaluatorError.

    Callers must therefore catch broadly, not only EvaluatorError.
    """
    with pytest.raises(Exception) as exc_info:
        simple_eval(expr, functions={"min": min})
    assert not isinstance(exc_info.value, EvaluatorError)
