from typing import Dict, Callable, Union, Any

from ..excs import NoSuchValue, NoSuchFunction
from .default import EvaluationUniverse


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
            raise NoSuchValue("No value {}".format(name))

    def evaluate_function(self, name, arg_getters):  # noqa: D102
        func = self.functions.get(name)
        if not func:
            raise NoSuchFunction("No function {}".format(name))
        return func(*[getter() for getter in arg_getters])
