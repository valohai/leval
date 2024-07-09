import pytest

from leval.excs import InvalidOperation, NoSuchValue, TooComplex
from leval.extras.common_boolean_evaluator import CommonBooleanEvaluator


@pytest.mark.parametrize(
    ("expression", "exception"),
    [
        ("+".join("a" * 500), TooComplex),
        ("b <", SyntaxError),
        ("os.system()", InvalidOperation),
    ],
)
def test_validation(expression, exception):
    with pytest.raises(exception):
        CommonBooleanEvaluator().verify(expression)
    with pytest.raises(exception):
        CommonBooleanEvaluator().evaluate(expression, {})


test_vars = {
    ("foo", "baz-quux"): 9,
    "continue": True,
    "v1": 74,
    "v2": 42,
}


@pytest.mark.parametrize(
    ("expression", "values", "expected"),
    [
        ("foo.baz-quux > 8", test_vars, True),  # dash in name
        ("foo.baz - quux > 8", test_vars, NoSuchValue),
        ("continue or not pause", test_vars, True),  # keyword
        ("cookie is None", test_vars, True),  # loose "is"
        ("not class", test_vars, True),  # loose "not"
        ("min(v1, v2) < 50", test_vars, True),
        ("max(v1, v2) > 50", test_vars, True),
        ("max()", test_vars, TypeError),
        ("max((1,2,3))", test_vars, TypeError),  # Invalid argument type (tuple)
    ],
)
def test_expressions(expression, values, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            CommonBooleanEvaluator().evaluate(expression, values)
    else:
        assert CommonBooleanEvaluator().evaluate(expression, values) == expected
