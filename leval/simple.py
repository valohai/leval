from __future__ import annotations

from typing import Any, Callable

from leval.evaluator import Evaluator
from leval.universe.simple import SimpleUniverse
from leval.universe.verifier import VerifierUniverse


def simple_eval(
    expression: str,
    *,
    functions: dict[str, Callable] | None = None,
    values: dict[str | tuple, Any] | None = None,
    max_depth=10,
    max_time: float | None = None,
    max_length: int | None = None,
    verify_only: bool = False,
):
    """
    Safely evaluate a simple expression.

    :param expression: A fragment of Python code.
    :param functions: Mapping of function names to functions.
    :param values: Mapping of value names to values.
    :param max_depth: Maximum expression depth (in terms of Python AST nodes).
    :param max_time: Maximum evaluation time in seconds.
    :param max_length: Maximum length of the expression string (0 to disable).
    :param verify_only: Only verify the expression in terms of allowed

    :return: The result of the evaluation.
    """
    universe: VerifierUniverse | SimpleUniverse
    if verify_only:
        universe = VerifierUniverse()
    else:
        universe = SimpleUniverse(functions=(functions or {}), values=(values or {}))
    se = Evaluator(
        universe,
        max_depth=max_depth,
        max_time=max_time,
        max_length=max_length,
    )
    return se.evaluate_expression(expression)
