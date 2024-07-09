import ast
import tokenize
from typing import List

import pytest

from leval.rewriter_utils import (
    convert_dash_identifiers,
    get_parts_from_dashed_identifier_tokens,
    make_glued_name_token,
)
from leval.utils import tokenize_expression


def converter(tokens: List[tokenize.TokenInfo]):
    if not tokens:
        return []
    glued_name = "".join(
        get_parts_from_dashed_identifier_tokens(tokens, separator="__"),
    )
    return [make_glued_name_token(tokens, glued_name)]


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("hello - world", None),
        ("foo-bar-baz-quux", "foo__bar__baz__quux"),
        ("foo-3bar-baz-quux", "foo__3bar__baz__quux"),
        ("foo-3.9bar", SyntaxError),  # decimals aren't allowed; invalid Python expr.
        ("foo-bar+baz-quux", "foo__bar+baz__quux"),
        ("foo-bar =='barf-glarf'", "foo__bar =='barf-glarf'"),
        ("foo-bar-baz- == 8", SyntaxError),  # ends with dash; no conversion but invalid
    ],
)
def test_convert_dash_identifiers(case, expected):
    should_raise_syntax_error = expected is SyntaxError
    if expected in (None, SyntaxError):  # shorthand for "no change expected"
        expected = case
    toks = list(tokenize_expression(case))
    converted = tokenize.untokenize(convert_dash_identifiers(toks, converter))
    assert converted == expected
    if should_raise_syntax_error:
        with pytest.raises(SyntaxError):
            ast.parse(converted)
    else:
        assert ast.parse(converted)
