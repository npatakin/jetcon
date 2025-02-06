from typing import Any

from jetcon.node import JetNode
from jetcon.context import JetContext
from jetcon.keywords import Keywords
from jetcon.merge import merge
from jetcon.read import read


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
    specs: list[str],
) -> JetNode:
    # empty node to write to
    _node = JetNode({})

    if isinstance(specs, str):
        specs = [specs]

    for spec in specs:
        # parse path and tag
        path, tag = _parse_imports(spec)
        # resolve path relative to current parent
        path = JetContext._resolve_path(path)

        # this if statement check circular import
        if JetContext._is_visited(str(path)):
            raise RuntimeError("Circular imports have been detected. "
                               f"The following config has import conflict: {path}")

        # add to file to visited stack for inner imports
        JetContext._add_visit(path)
        # read and compose inner configs
        new_node = read(path, compose=True, reset=False)
        # remove path from visited stack, since
        # we may want to import the same file in different tree node
        JetContext._rm_visit(path)

        # if tagged import -> use it as key
        if tag is not None:
            # new_node = JetNode({tag: new_node}, recursive=False)
            sub_node = new_node
            for sub_tag in tag.split('.'):
                try:
                    sub_node = sub_node.get(sub_tag)
                except:
                    raise ValueError('Failed to resolve import key "{}" '
                                     'for "" path. Sub tag {} not found'.format(
                        tag, path, sub_tag))
            merge(_node, sub_node)
        else:
            merge(_node, new_node)
            # node.update(**new_node)
    # revert context parameters from parent node
    # parent node parameters have higher priority
    return merge(_node, node)


def _compose_node(
    node: JetNode,
    recursive: bool = True
) -> dict:
    return JetNode({k: _compose(v, recursive) for k, v in node.items()})


def _compose_list(
    lst: list,
    recursive: bool = True
) -> list:
    return [_compose(v, recursive) for v in lst]


def _compose(
    node: Any,
    recursive: bool = True
) -> Any:
    if isinstance(node, list):
        return _compose_list(node, recursive)

    if isinstance(node, JetNode):
        return compose(node, recursive)

    return node


def compose(
    node: JetNode,
    recursive: bool = True
) -> JetNode:
    if recursive:
        node = _compose_node(node, recursive)

    kw = Keywords.imports.value

    if kw in node:
        return _compose_imports(specs=node.pop(kw), node=node)
    return node
