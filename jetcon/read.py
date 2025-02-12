import yaml     # type: ignore
from pathlib import Path
from typing import Callable

from jetcon.context import JetContext
from jetcon.node import JetNode


# This registry maps extenstions to reader functions.
# Each reader function takes a string path and compose flag,
# that regulate _import_ behavior (True = import and merge).
READERS = dict()


def register_reader(
    ext: str,
    reader: Callable[[Path], JetNode]
) -> None:
    """
    Registers a reader function for a given file extension.

    Parameters
    ----------
    ext : str
        The file extension to associate with the reader function.
    reader : Callable[[Path | str], JetNode]
        The reader function to register.

    Returns
    -------
    None
    """
    READERS[ext] = reader


def read_yaml(
    path: Path
) -> JetNode:
    # resolver is specified in global read call
    # so, just use it here to resolve relatives
    # if not path.is_absolute():
    #     parent = JetContext._get_resolver()
    #     path = (Path(parent) / path).resolve()

    # load and construct JetNode
    with path.open("r") as file:
        tree = yaml.safe_load(file)
    return JetNode(tree)


register_reader(".yaml", read_yaml)
register_reader(".yml", read_yaml)


def read(
    path: str | Path,
    compose: bool = True
) -> JetNode:
    if not isinstance(path, Path):
        path = Path(path)
    if not path.is_absolute():
        path = path.resolve()

    ext = path.suffix.lower()
    reader = READERS.get(ext, None)

    if reader is None:
        raise ValueError(f"Cannot read from file with {ext}.")

    JetContext._add_visit(path)
    # read title config and compose it recursively
    try:
        tree = reader(path)
        if compose:
            # import it here instead of top level due to circular imports
            from jetcon.compose import compose as _compose
            from jetcon.interpolate import interpolate as _interpolate
            tree = _compose(tree)
            tree = _interpolate(tree)
        # free deps stack
    except Exception as e:
        raise RuntimeError('Exception occurred during config "{}" reading'.format(path))
    finally:
        JetContext._rm_visit(path)

    return tree
