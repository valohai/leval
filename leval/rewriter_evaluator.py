import ast
import io
import keyword
import tokenize
from typing import Iterable

from leval.evaluator import Evaluator

# Keyword-like elements that can be used in an expression.
EXPRESSION_KEYWORDS = {
    "False",
    "None",
    "True",
    "and",
    "for",
    "in",
    "is",
    "not",
    "or",
}


def _tokenize_expression(expression: str) -> Iterable[tokenize.TokenInfo]:
    return tokenize.generate_tokens(io.StringIO(expression).readline)


class RewriterEvaluator(Evaluator):
    def parse(self, expression: str) -> ast.AST:
        """
        Possibly rewrite, then parse the expression and return the AST.
        """
        try:
            expression = self.rewrite_expression(expression)
        except tokenize.TokenError:
            pass  # Will be raised as a SyntaxError by ast.parse.
        return super().parse(expression)

    def rewrite_expression(self, expression: str) -> str:
        """
        Rewrite an expression before parsing.

        This is useful for rewriting code that are not valid Python
        expressions (e.g. containing suites or reserved keywords).
        """
        bits = []
        for tok in _tokenize_expression(expression):
            if (
                tok.type == tokenize.NAME
                and keyword.iskeyword(tok.string)
                and tok.string not in EXPRESSION_KEYWORDS
            ):
                tok = tok._replace(string=self.rewrite_keyword(tok.string))
            bits.append(tok)
        expression = tokenize.untokenize(bits)
        return expression

    def rewrite_keyword(self, kw: str) -> str:
        """
        Return the replacement for the given keyword.
        """
        raise SyntaxError(f"Keyword {kw!r} can not be used")  # pragma: no cover
