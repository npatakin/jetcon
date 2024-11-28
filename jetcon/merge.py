import re
from typing import Any

from jetcon.node import JetNode


DO_NOT_MERGE = "!"

EXTRACT_PATTERN = re.compile("[a-z0-9_]+", re.IGNORECASE)


def _mergable(
    key: str
) -> None:
    return key[-1] != DO_NOT_MERGE


def _get(
    key: str,
    node: JetNode
) -> Any:
    key = _key(key)
    if key in node:
        return node[key], key
    else:
        return node[key + DO_NOT_MERGE], key + DO_NOT_MERGE


def _key(
    key: str
) -> str:
    matches = re.findall(EXTRACT_PATTERN, key)
    if len(matches) > 1:
        raise SyntaxError(f"Undefinded key syntax: {key}")
    return matches[0]


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
        del node[key + DO_NOT_MERGE]
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
        print(sv, dv)
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
