from __future__ import annotations
from adict import adict     # type: ignore
from pathlib import Path

from jetcon.context import JetContext
from jetcon.io import read_yaml


class JetNode(adict):
    def __init__(
        self,
        cfg: dict = {},
        recursive: bool = True
    ) -> None:
        # create nodes recursively
        if recursive:
            for key, value in cfg.items():
                if isinstance(value, dict):
                    cfg[key] = JetNode(value)

                if isinstance(value, list):
                    _value = []
                    for _v in value:
                        if isinstance(_v, dict):
                            _v = JetNode(_v)
                        _value.append(_v)
                    cfg[key] = _value

        # use adict constructor
        super().__init__(cfg)

    @staticmethod
    def from_yaml(
        path: str
    ) -> JetNode:
        # resolve absolute path from relative
        path = Path(path)

        if not path.is_absolute():
            parent = JetContext._get_resolver()
            path = (Path(parent) / path).resolve()

        # read raw yaml
        tree = read_yaml(path)
        # recursively create nodes
        node = JetNode(tree)
        return node
