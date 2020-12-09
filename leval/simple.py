from typing import Dict, Callable, Union, Any

from .evaluator import Evaluator
from .excs import NoSuchFunction, NoSuchValue
from .universe import EvaluationUniverse


class SimpleUniverse(EvaluationUniverse):
    def __init__(
        self, *, functions: Dict[str, Callable], values: Dict[Union[str, tuple], Any]
    ):
        """
        Initialize a simple evaluation universe.

        The values may be keyed by strings or tuples of strings.
        Tuples of strings are used for dotted attribute access.

        :param functions: Mapping of function names to functions.
        :param values: Mapping of value names to values.
        """
        super().__init__()
        self.functions = functions
        self.values = values

    def get_value(self, name):  # noqa: D102
        try:
            return self.values[name]
        except KeyError:
            raise NoSuchValue(f"No value {name}")

    def evaluate_function(self, name, arg_getters):  # noqa: D102
        func = self.functions.get(name)
        if not func:
            raise NoSuchFunction(f"No function {name}")
        return func(*[getter() for getter in arg_getters])


def simple_eval(
    expression: str,
    *,
    functions: Dict[str, Callable] = None,
    values: Dict[Union[str, tuple], Any] = None,
    max_depth=10,
):
    """
    Safely evaluate a simple expression.

    :param expression: A fragment of Python code.
    :param functions: Mapping of function names to functions.
    :param values: Mapping of value names to values.
    :param max_depth: Maximum expression depth (in terms of Python AST nodes).

    :return: The result of the evaluation.
    """
    se = Evaluator(SimpleUniverse(functions=(functions or {}), values=(values or {})))
    se.max_depth = max_depth
    return se.evaluate_expression(expression)
