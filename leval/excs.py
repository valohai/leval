import ast
from typing import Optional


class EvaluatorError(Exception):
    def __init__(self, message: str, *, node: Optional[ast.AST] = None) -> None:
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


class NoSuchValue(NameError, EvaluatorError):
    pass


class NoSuchFunction(NameError, EvaluatorError):
    pass


class TooComplex(EvaluatorError):
    pass
