import re
from typing import Any

from jetcon.node import JetNode


ESCAPE_CHAR = "!"

# usefull to extract string name without '!'
EXTRACT_PATTERN = re.compile("[a-z0-9_]+", re.IGNORECASE)

# usefull to check if section is mergable
MERGABLE_PATTERN = re.compile("[a-z0-9_]+!", re.IGNORECASE)

# usefull to check syntax
SYNTAX_PATTERN = re.compile("[a-z0-9_]+!?", re.IGNORECASE)


def _mergable(
    key: str
) -> None:
    return not bool(re.fullmatch(MERGABLE_PATTERN, key))   # key[-1] != ESCAPE_CHAR


def _get(
    key: str,
    node: JetNode
) -> Any:
    key = _key(key)
    if key in node:
        return node[key], key
    else:
        return node[key + ESCAPE_CHAR], key + ESCAPE_CHAR


def _key(
    key: str
) -> str:
    if re.fullmatch(SYNTAX_PATTERN, key) is None:
        raise SyntaxError(f"Undefinded key syntax: {key}")
    return re.findall(EXTRACT_PATTERN, key)[0]


def _keys(
    node: JetNode
) -> set[str]:
    return {_key(k) for k in node}


def _replace(
    node: JetNode,
    key: str,
    value: Any
) -> JetNode:
    if key in node:
        node[key] = value
    else:
        del node[key + ESCAPE_CHAR]
        node[key] = value

    return node


def merge(
    dst: JetNode,
    src: JetNode
) -> JetNode:
    # intersection
    for k in _keys(src) & _keys(dst):
        sv, sk = _get(k, src)
        dv, dk = _get(k, dst)
        if isinstance(sv, JetNode) and isinstance(dv, JetNode):
            if _mergable(sk):
                _replace(dst, dk, merge(dv, sv))
            else:
                _replace(dst, dk, sv)
        else:
            _replace(dst, dk, sv)

    # difference
    for k in _keys(src) - _keys(dst):
        sv, _ = _get(k, src)
        dst[k] = sv

    return dst
