from pathlib import Path
# from copy import deepcopy
from typing import Callable

from jetcon.node import JetNode
from jetcon.context import JetContext
from jetcon.keywords import Keywords
from jetcon.merge import merge


COMPOSERS = dict()


def register_composer(
    keyword: str,
    composer: Callable[[str, list[str]], JetNode]
) -> None:
    """
    Registers a composer function for a given keyword.

    Parameters
    ----------
    keyword : str
        The keyword to associate with the composer function.
    builder : Callable[[str, dict[str, Any]], Any]
        The composer function to register.

    Returns
    -------
    None
    """
    COMPOSERS[keyword] = composer


def _parse_imports(
    spec: str
) -> tuple[str, str]:
    # remove whitespaces
    _spec = spec.replace(" ", "")
    # find split around @
    _spec = _spec.split("@")

    if len(_spec) > 2:
        # syntax error, the regular import shold be like this:
        # - ./config1.yaml @ tag
        # - ./config2.yaml
        raise RuntimeError(f"Undefinded import string format: {spec}. "
                           "Please, fix this according to import syntax: "
                           " '- ./path_to_config.yaml @ tag'")

    # wrap it with dict, needed to call get with default value
    # default values are not supported by python lists, for some reason
    _spec = dict(enumerate(_spec))
    return _spec.get(0), _spec.get(1, None)


def _compose_imports(
    node: JetNode,
    specs: list[str]
) -> JetNode:
    # empty node to write to
    _node = JetNode({})

    for spec in specs:
        # parse path and tag
        path, tag = _parse_imports(spec)

        parent = JetContext._get_resolver()
        # resolved path to file to be imported
        path = str((Path(parent) / path).resolve())

        # this if statement check circular import
        if JetContext._is_visited(path):
            raise RuntimeError("Circular imports have been detected. "
                               f"The following config has import conflict: {path}")

        # add to file to visited stack for inner imports
        JetContext._add_visit(path)
        # read and compose inner configs
        new_node = JetNode.from_yaml(path)
        # compose with modified visited stack
        new_node = compose(new_node)
        # remove path from visited stack, since
        # we may want to import the same file in different tree node
        JetContext._rm_visit(path)

        # if tagged import -> use it as key
        if tag is not None:
            new_node = JetNode({tag: new_node}, recursive=False)
            merge(_node, new_node)
        else:
            merge(_node, new_node)
            # node.update(**new_node)
    # revert context parameters from parent node
    # parent node parameters have higher priority
    return merge(_node, node)


register_composer(Keywords.imports.value, _compose_imports)


def _resolve_composer(
    node: JetNode
) -> str | None:
    # find specified keywords
    specified = node.keys() & COMPOSERS.keys()

    # only one builder is allowed for a single node
    if len(specified) > 1:
        raise RuntimeError("Multiple composers have been detected. "
                           f"Incorrect node: {node}.")
    # if set is empty, then this is a simple node
    # simple nodes are not supposed to be rebuild via callable
    if len(specified) == 0:
        return None

    # remaining key set contains single element
    return specified.pop()


def compose(
    node: JetNode,
    recursive: bool = True
) -> JetNode:
    if recursive:
        # recursively build inner nodes first
        for key, value in node.items():
            if isinstance(value, JetNode):
                node[key] = compose(value)

            if isinstance(value, list):
                _value = []
                for _v in value:
                    if isinstance(_v, JetNode):
                        _v = compose(_v)
                    _value.append(_v)
                node[key] = _value

    kw = _resolve_composer(node)

    if kw is not None:
        return COMPOSERS[kw](specs=node.pop(kw), node=node)
    return node
