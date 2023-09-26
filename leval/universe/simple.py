from typing import Any, Callable, Dict, Union

from leval.excs import NoSuchFunction, NoSuchValue
from leval.universe.default import EvaluationUniverse


class SimpleUniverse(EvaluationUniverse):
    def __init__(
        self,
        *,
        functions: Dict[str, Callable],
        values: Dict[Union[str, tuple], Any],
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
            raise NoSuchValue(f"No value {name}") from None

    def evaluate_function(self, name, arg_getters):  # noqa: D102
        func = self.functions.get(name)
        if not func:
            raise NoSuchFunction(f"No function {name}")
        return func(*[getter() for getter in arg_getters])
