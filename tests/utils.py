import dataclasses
import filecmp
import inspect
import sys
from collections.abc import Callable, Mapping
from inspect import Parameter
from pathlib import Path, PurePath
from shutil import copy as sh_copy
from shutil import copytree
from typing import Any, Final

sys.path.append(str(PurePath(__file__).parents[1]))

from functions import Copy

DATA_DIRS: Final[tuple[Path]] = tuple((Path(__file__).parent / "data").iterdir())


def replace_dataclass(dc, **kwargs):
    """
    An alternative to `dataclasses.replace` that also takes
    positonal-only `__init__` arguments into account
    """
    as_dict: Final[Mapping[str, Any]] = dataclasses.asdict(dc)
    positional_only: Final[list[Any]] = []

    for k, v in kwargs.items():
        if k in as_dict:
            as_dict[k] = v

    constructor: Callable = type(dc)

    for name, param in inspect.signature(constructor).parameters.items():
        if param.kind == Parameter.POSITIONAL_ONLY:
            positional_only.append(as_dict.pop(name))

    output = constructor(*positional_only, **as_dict)
    return output


def copy_to(copyobj: Copy, output_dir: Path) -> None:
    if copyobj.path.is_dir():
        copytree(copyobj.path, output_dir / copyobj.path.name)
    else:
        sh_copy(copyobj.path, output_dir)


def equal_trees(dir1, dir2):
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if dirs_cmp.left_only or dirs_cmp.right_only or dirs_cmp.funny_files:
        return False

    if any(filecmp.cmpfiles(dir1, dir2, dirs_cmp.common_files, shallow=False)[1:]):
        return False

    for common_dir in dirs_cmp.common_dirs:
        if not are_dir_trees_equal(dir1 / common_dir, dir2 / common_dir):
            return False
    return True


def filled_children(copyobj, *args, **kwargs):
    if not copyobj.path.is_dir():
        return copyobj

    children: frozenset[Copy] = frozenset(
        map(
            filled_children,
            (Copy(path, *args, **kwargs) for path in copyobj.path.iterdir()),
        )
    )
    return replace_dataclass(copyobj, children=children)
