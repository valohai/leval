import tokenize
from typing import Callable, Iterable, Iterator, List, Optional


def tokens_are_adjacent(t1: tokenize.TokenInfo, t2: tokenize.TokenInfo) -> bool:
    """
    Return True if the two tokens are adjacent in the source code.

    That is, token 1 ends exactly where token 2 starts.
    """
    return t1.end[0] == t2.start[0] and t1.end[1] == t2.start[1]


def make_glued_name_token(tokens: List[tokenize.TokenInfo], name: str):
    """
    Create a new token for an identifier that spans the given token position range.

    It does not validate that the resulting token is actually a valid Python identifier,
    or that the range is actually valid (`name` could be longer than the range of the
    original tokens).
    """
    stok = tokens[0]
    etok = tokens[-1]
    return tokenize.TokenInfo(
        tokenize.NAME,
        name,
        stok.start,
        etok.end,
        stok.line,
    )


def get_parts_from_dashed_identifier_tokens(
    tokens: Iterable[tokenize.TokenInfo],
    separator: Optional[str] = None,
) -> Iterable[str]:
    """
    Yield the parts of a dashed identifier from the given token stream.

    If `separator` is set, it is yielded for dashes in the identifier.
    """
    for tok in tokens:
        if tok.type in (tokenize.NAME, tokenize.NUMBER):
            yield tok.string
        elif tok.type == tokenize.OP and tok.string == "-":
            if separator:
                yield separator
            continue
        else:
            raise SyntaxError("Invalid token")


def _maybe_process_dash_identifier(
    initial_token: tokenize.TokenInfo,
    tok_iter: Iterator[tokenize.TokenInfo],
    converter: Callable[[List[tokenize.TokenInfo]], Iterable[tokenize.TokenInfo]],
):
    tokens = [initial_token]
    while True:
        tok = next(tok_iter, None)
        if tok is None:
            break
        if not tokens_are_adjacent(tokens[-1], tok):
            break
        if (
            tok.type == tokenize.NAME
            or (tok.type == tokenize.OP and tok.string == "-")
            or (tok.type == tokenize.NUMBER and tok.string.isdigit())
        ):
            tokens.append(tok)
        else:
            break
    if tokens:  # Yield the converted token(s) if there are tokens to convert.
        if tokens[-1].type == tokenize.OP:  # ended with a dash? no conversion
            yield from tokens
        else:
            yield from converter(tokens)
    if tok:  # Yield the last token that broke the loop.
        yield tok


def convert_dash_identifiers(
    tokens: List[tokenize.TokenInfo],
    converter: Callable[[List[tokenize.TokenInfo]], Iterable[tokenize.TokenInfo]],
) -> Iterable[tokenize.TokenInfo]:
    """
    Convert dashed identifiers in the given token stream.

    In particular, converts e.g. `foo-bar-baz-quux` that is actually
    `NAME OP(-) NAME (...)` with no spaces in between, into a single
    token via the given converter function.
    """
    tok_iter = iter(tokens)

    while True:
        tok = next(tok_iter, None)
        if tok is None:
            break
        if tok.type == tokenize.NAME:  # Could be the start of a dashed identifier.
            yield from _maybe_process_dash_identifier(tok, tok_iter, converter)
            continue
        yield tok
