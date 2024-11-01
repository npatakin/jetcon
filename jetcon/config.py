
from pathlib import Path

from jetcon.context import JetContext
from jetcon.node import JetNode
from jetcon.builder import build
from jetcon.composer import compose


class JetConfig:
    def __init__(self) -> None:
        raise RuntimeError(f"Class {JetConfig.__name__} cannot be instansiated. "
                           "Use .from_*() methods to create config tree.")

    @staticmethod
    def build(
        cfg: JetNode
    ) -> JetNode:
        return build(cfg)

    @staticmethod
    def from_yaml(
        path: str
    ) -> JetNode:
        path = Path(path)

        if not path.is_absolute():
            path = path.resolve()

        # update global path resolver
        JetContext._set_resolver(str(path.parent))

        # make typecheckers happy
        path = str(path)
        # add deps to stack
        JetContext._add_visit(path)
        # read title config and compose it recursively
        tree = JetNode.from_yaml(path)
        tree = compose(tree)
        # free deps stack
        JetContext._rm_visit(path)

        return tree
