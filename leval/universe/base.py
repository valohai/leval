import ast
from typing import Any, Callable, List, Tuple, Union

from leval.excs import InvalidOperation, NoSuchFunction, NoSuchValue


class BaseEvaluationUniverse:
    def get_value(self, name: Union[str, Tuple[str]]) -> Any:
        """
        Get the value for a given name.

        The value is a tuple if the original identifier had been a dotted name.
        Otherwise it is a string.
        """
        raise NoSuchValue(f"No value {name}")  # pragma: no cover

    def evaluate_function(self, name: str, arg_getters: List[Callable[[], Any]]) -> Any:
        """
        Evaluate a function with the given arguments.

        Invoke the functions in `arg_getters` to acquire
        the true values of the arguments.
        """
        raise NoSuchFunction(f"No function {name}")  # pragma: no cover

    def evaluate_binary_op(  # noqa: D102
        self,
        op: ast.AST,
        left: Any,
        right: Any,
    ) -> Any:
        raise InvalidOperation(  # pragma: no cover
            f"Binary operator {op} is not allowed",
            node=op,
        )

    def evaluate_bool_op(self, op: ast.AST, value_getters: List[Callable[[], Any]]):
        """
        Evaluate a boolean operation with the given arguments.

        Invoke the functions in `value_getters` to acquire
        the true values of the values being compared.
        """
        raise InvalidOperation(  # pragma: no cover
            f"Boolean operator {op} is not allowed",
            node=op,
        )
