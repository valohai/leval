import ast
import functools
import operator
from numbers import Number
from typing import Any, List, Callable

from .base import BaseEvaluationUniverse
from ..excs import InvalidOperation, InvalidOperands


def numbers_only_binop(name, func):
    """
    Decorate `func` to ensure its two arguments are numbers.
    """

    @functools.wraps(func)
    def binop(a, b):
        if not (isinstance(a, Number) and isinstance(b, Number)):
            raise InvalidOperands(
                'operator "{name}" can only be used with numbers, not {a!r} and {b!r}'.format(
                    name=name,
                    a=a,
                    b=b,
                )
            )
        return func(a, b)

    return binop


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


class EvaluationUniverse(BaseEvaluationUniverse):
    ops = DEFAULT_OPS

    def evaluate_binary_op(  # noqa: D102
        self, op: ast.AST, left: Any, right: Any
    ) -> Any:
        bin_op = self.ops.get(type(op))
        if not bin_op:
            raise InvalidOperation(  # pragma: no cover
                "Binary operator {} is not allowed".format(op), node=op
            )
        return bin_op(left, right)

    def evaluate_bool_op(self, op: ast.AST, value_getters: List[Callable[[], Any]]):
        if isinstance(op, ast.And):
            return all(g() for g in value_getters)
        if isinstance(op, ast.Or):
            return any(g() for g in value_getters)
        raise InvalidOperation(  # pragma: no cover
            "Boolean operator {} is not allowed".format(op), node=op
        )
