import functools
from numbers import Number

from leval.excs import InvalidOperands


def numbers_only_binop(name, func):
    """
    Decorate `func` to ensure its two arguments are numbers.
    """

    @functools.wraps(func)
    def binop(a, b):
        if not (isinstance(a, Number) and isinstance(b, Number)):
            raise InvalidOperands(
                f'operator "{name}" can only be used with numbers, not {a!r} and {b!r}'
            )
        return func(a, b)

    return binop
