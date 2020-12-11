from typing import Dict, Callable, Union, Any

from .evaluator import Evaluator
from .universe.simple import SimpleUniverse
from .universe.verifier import VerifierUniverse


def simple_eval(
    expression: str,
    *,
    functions: Dict[str, Callable] = None,
    values: Dict[Union[str, tuple], Any] = None,
    max_depth=10,
    verify_only: bool = False,
):
    """
    Safely evaluate a simple expression.

    :param expression: A fragment of Python code.
    :param functions: Mapping of function names to functions.
    :param values: Mapping of value names to values.
    :param max_depth: Maximum expression depth (in terms of Python AST nodes).
    :param verify_only: Only verify the expression in terms of allowed

    :return: The result of the evaluation.
    """
    if verify_only:
        universe = VerifierUniverse()
    else:
        universe = SimpleUniverse(functions=(functions or {}), values=(values or {}))
    se = Evaluator(universe, max_depth=max_depth)
    return se.evaluate_expression(expression)
