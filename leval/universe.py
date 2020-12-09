import ast
import operator
from typing import Union, Tuple, Any, Callable, List

from .excs import NoSuchValue, NoSuchFunction, InvalidOperation
from .utils import numbers_only_binop

DEFAULT_OPS = {
    ast.Add: numbers_only_binop("add", operator.add),
    ast.Sub: numbers_only_binop("sub", operator.sub),
    ast.Mult: numbers_only_binop("mul", operator.mul),
    ast.Div: numbers_only_binop("div", operator.truediv),
    ast.FloorDiv: numbers_only_binop("fdiv", operator.floordiv),
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}


class EvaluationUniverse:
    ops = DEFAULT_OPS

    def get_value(self, name: Union[str, Tuple[str]]) -> Any:
        """
        Get the value for a given name (either a string or a tuple,
        if the original identifier had been a dotted name).
        """
        raise NoSuchValue(f"No value {name}")  # pragma: no cover

    def evaluate_function(self, name: str, arg_getters: List[Callable[[], Any]]) -> Any:
        """
        Evaluate a function with the given arguments.
        Invoke the functions in `arg_getters` to acquire the true values of the arguments.
        """
        raise NoSuchFunction(f"No function {name}")  # pragma: no cover

    def evaluate_binary_op(self, op: ast.AST, left: Any, right: Any) -> Any:
        bin_op = self.ops.get(type(op))
        if not bin_op:
            raise InvalidOperation(  # pragma: no cover
                f"Binary operator {op} is not allowed", node=op
            )
        return bin_op(left, right)

    def evaluate_bool_op(self, op: ast.AST, value_getters: List[Callable[[], Any]]):
        """
        Evaluate a function with the given arguments.
        Invoke the functions in `value_getters` to acquire the true values of the values being compared.
        """
        if isinstance(op, ast.And):
            return all(g() for g in value_getters)
        if isinstance(op, ast.Or):
            return any(g() for g in value_getters)
        raise InvalidOperation(  # pragma: no cover
            f"Boolean operator {op} is not allowed", node=op
        )
