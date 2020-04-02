class EvaluatorError(Exception):
    pass


class InvalidOperation(EvaluatorError):
    pass


class InvalidNode(InvalidOperation):
    pass


class InvalidOperands(InvalidOperation):
    pass


class NoSuchValue(NameError, EvaluatorError):
    pass


class NoSuchFunction(NameError, EvaluatorError):
    pass


class TooComplex(EvaluatorError):
    pass
