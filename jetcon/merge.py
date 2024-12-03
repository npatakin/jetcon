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


def _merge(
    dst: Any,
    src: Any
) -> Any:
    if isinstance(dst, JetNode) and isinstance(src, JetNode):
        return _merge_nodes(dst, src)

    if isinstance(dst, list) and isinstance(src, list):
        return _merge_lists(dst, src)
    # cannot merge other type, so just replace
    return src


def _merge_lists(
    dst: list,
    src: list
) -> list:

    last_ = 0
    # intersection
    for k, _ in enumerate(zip(dst, src)):
        dst[k] = _merge(dst[k], src[k])
        last_ = k + 1

    # difference
    for k in range(last_, len(src)):
        dst.append(src[k])

    return dst


def _merge_nodes(
    dst: JetNode,
    src: JetNode
) -> JetNode:
    # intersection
    for k in _keys(src) & _keys(dst):
        sv, sk = _get(k, src)
        dv, dk = _get(k, dst)

        if _mergable(sk):
            _replace(dst, dk, _merge(dv, sv))
        else:
            _replace(dst, dk, sv)

    # difference
    for k in _keys(src) - _keys(dst):
        sv, _ = _get(k, src)
        dst[k] = sv

    return dst


def merge(
    dst: JetNode,
    src: JetNode
) -> JetNode:
    return _merge_nodes(dst, src)
