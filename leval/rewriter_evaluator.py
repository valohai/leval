import ast
import keyword
import tokenize
from typing import Iterable, List

from leval.evaluator import Evaluator
from leval.utils import tokenize_expression

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
        tokens = tokenize_expression(expression)
        tokens = list(self.rewrite_keywords(tokens))
        return tokenize.untokenize(self.process_tokens(tokens))

    def rewrite_keywords(
        self,
        tokens: Iterable[tokenize.TokenInfo],
    ) -> Iterable[tokenize.TokenInfo]:
        """
        Do a keyword-rewriting pass on the tokens.
        """
        for tok in tokens:
            if (
                tok.type == tokenize.NAME
                and keyword.iskeyword(tok.string)
                and tok.string not in EXPRESSION_KEYWORDS
            ):
                tok = tok._replace(string=self.rewrite_keyword(tok.string))
            yield tok

    def rewrite_keyword(self, kw: str) -> str:
        """
        Return the replacement for the given keyword.
        """
        raise SyntaxError(f"Keyword {kw!r} can not be used")  # pragma: no cover

    def process_tokens(
        self,
        tokens: List[tokenize.TokenInfo],
    ) -> Iterable[tokenize.TokenInfo]:
        """
        Process the token stream before untokenizing it back to a string.

        Does nothing by default, but can be overridden.
        """
        return tokens
