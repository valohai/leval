import ast
from typing import Optional


class EvaluatorError(Exception):
    def __init__(  # noqa: D107
        self,
        message: str,
        *,
        node: Optional[ast.AST] = None,
    ) -> None:
        super().__init__(message)
        self.node = node


class InvalidOperation(EvaluatorError):
    pass


class InvalidNode(InvalidOperation):
    pass


class InvalidConstant(InvalidOperation):
    pass


class InvalidOperands(InvalidOperation):
    pass


class InvalidAttribute(InvalidOperation):
    pass


class NoSuchValue(NameError, EvaluatorError):
    pass


class NoSuchFunction(NameError, EvaluatorError):
    pass


class TooComplex(EvaluatorError):
    pass


class Timeout(EvaluatorError, TimeoutError):
    pass
