from typing import Dict, Callable, Union, Any

from .evaluator import Evaluator
from .excs import NoSuchFunction, NoSuchValue
from .universe import EvaluationUniverse


class SimpleUniverse(EvaluationUniverse):
    def __init__(
        self, *, functions: Dict[str, Callable], values: Dict[Union[str, tuple], Any]
    ):
        super().__init__()
        self.functions = functions
        self.values = values

    def get_value(self, name):
        try:
            return self.values[name]
        except KeyError:
            raise NoSuchValue(f"No value {name}")

    def evaluate_function(self, name, arg_getters):
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
    se = Evaluator(SimpleUniverse(functions=(functions or {}), values=(values or {})))
    se.max_depth = max_depth
    return se.evaluate_expression(expression)
