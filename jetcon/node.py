from __future__ import annotations
from adict import adict     # type: ignore
from copy import deepcopy
from typing import Any, Callable


def _dict_to_node(
    dct: dict
) -> dict:
    return {k: _to_node(v) for k, v in dct.items()}


def _list_to_node(
    lst: list
) -> list:
    return [_to_node(v) for v in lst]


def _to_node(
    node: Any
) -> Any:
    if isinstance(node, list):
        return _list_to_node(node)

    if isinstance(node, dict):
        return JetNode(_dict_to_node(node))

    return node


class JetNode(adict):
    def __init__(
        self,
        cfg: dict | list = {},
        recursive: bool = True
    ) -> None:
        # case when yaml reader return list instead of dict
        if isinstance(cfg, list):
            cfg = {i: cfg[i] for i in range(cfg)}

        # create nodes recursively
        if recursive:
            cfg = _dict_to_node(cfg)
        # use adict constructor
        super().__init__(cfg)

    @staticmethod
    def read(
        path: str
    ) -> JetNode:
        from jetcon.read import read
        return read(path, reset=True, compose=True)

    def build(
        self,
        partial: bool = True
    ) -> Any:
        from jetcon.build import build
        # build copied version to be able to secure the original tree
        return build(deepcopy(self), recursive=True, partial=partial)

    def cast(
        self,
        factory: Callable,
    ) -> Any:
        from jetcon.cast import cast
        return cast(deepcopy(self), factory=factory)

    def to_dict(
        self
    ) -> dict:
        from jetcon.cast import to_dict
        return to_dict(deepcopy(self), recursive=True)

    def merge(
        self,
        node: JetNode
    ) -> JetNode:
        from jetcon.merge import merge
        return merge(self, node)

    def save(
        self,
        path: str
    ) -> None:
        from jetcon.save import save
        return save(self, path=path)
