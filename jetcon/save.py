import yaml     # type: ignore
from pathlib import Path
from typing import Callable

from jetcon.node import JetNode
from jetcon.cast import to_dict


SAVERS = dict()


def register_saver(
    ext: str,
    saver: Callable[[Path, dict], None]
) -> None:
    """
    Registers a saver function for a given file extension.

    Parameters
    ----------
    ext : str
        The file extension to associate with the saver function.
    saver : Callable[[Path, dict], None]
        The saver function to register.

    Returns
    -------
    None
    """
    SAVERS[ext] = saver


def save_yaml(
    node: dict,
    path: Path
) -> None:
    if path.exists():
        raise ValueError(f"File already exists: {str(path)}")

    with path.open("w") as file:
        yaml.dump(node, file)


register_saver(".yaml", save_yaml)
register_saver(".yml", save_yaml)


def save(
    node: JetNode,
    path: str | Path
) -> None:
    if not isinstance(path, Path):
        path = Path(path)

    tree = to_dict(node, recursive=True)
    ext = path.suffix.lower()

    return SAVERS[ext](tree, path)
