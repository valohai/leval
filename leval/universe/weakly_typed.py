import ast
import functools
import operator

from .default import EvaluationUniverse
from .simple import SimpleUniverse
from ..excs import InvalidOperands


def weakly_typed_operation(func, coerce=float, check=None):
    """
    Make the wrapped function "weakly typed"; it first attempts to use the arguments
    as is for the function, and failing that, coerces them using the given function first.

    The optional check function is run before each invocation of func.
    """

    def checked_call(args):
        if check:
            check(args)
        return func(*args)

    @functools.wraps(func)
    def op(*operands):
        try:
            return checked_call(operands)
        except (TypeError, ValueError):
            try:
                return checked_call([coerce(x) for x in operands])
            except Exception:
                pass
            raise

    return op


def guard_no_string_mul(args):
    if any(isinstance(a, str) for a in args):
        raise InvalidOperands("can't multiply strings")


class WeaklyTypedEvaluationUniverse(EvaluationUniverse):
    ops = {
        ast.Add: weakly_typed_operation(operator.add),
        ast.Sub: weakly_typed_operation(operator.sub),
        ast.Mult: weakly_typed_operation(operator.mul, check=guard_no_string_mul),
        ast.Div: weakly_typed_operation(operator.truediv),
        ast.FloorDiv: weakly_typed_operation(operator.floordiv),
        ast.Gt: weakly_typed_operation(operator.gt),
        ast.GtE: weakly_typed_operation(operator.ge),
        ast.Eq: weakly_typed_operation(operator.eq),
        ast.NotEq: weakly_typed_operation(operator.ne),
        ast.Lt: weakly_typed_operation(operator.lt),
        ast.LtE: weakly_typed_operation(operator.le),
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
    }


class WeaklyTypedSimpleUniverse(WeaklyTypedEvaluationUniverse, SimpleUniverse):
    pass
