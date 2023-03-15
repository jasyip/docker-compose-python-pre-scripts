import filecmp
import inspect
import sys
from collections.abc import Callable
from inspect import Parameter
from pathlib import Path, PurePath
from shutil import copy as sh_copy
from shutil import copytree
from typing import Any, NamedTuple

sys.path.append(str(PurePath(__file__).parents[1]))

from functions import Copy


def replace_namedtuple(nt: NamedTuple, **kwargs) -> NamedTuple:
    """
    An alternative to `namedtuple._replace` that invokes `namedtuple.__new__` code behavior
    """
    as_dict: dict[str, Any] = nt._asdict()
    positional_only: list[Any] = []

    for k, v in kwargs.items():
        if k in as_dict:
            as_dict[k] = v

    constructor: Callable = type(nt)

    for name, param in inspect.signature(constructor).parameters.items():
        if param.kind == Parameter.POSITIONAL_ONLY:
            positional_only.append(as_dict.pop(name))

    return constructor(*positional_only, **as_dict)


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
