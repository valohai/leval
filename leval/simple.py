from typing import Dict, Callable, Union, Any

from .evaluator import Evaluator
from .universe.simple import SimpleUniverse


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
