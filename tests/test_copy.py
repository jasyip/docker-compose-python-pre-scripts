import grp
import pwd
import random
import re
import sys
from collections import ChainMap
from collections.abc import Callable, Sequence
from pathlib import Path, PurePath
from shutil import rmtree
from typing import Optional, Union
from warnings import warn

import pytest

import utils

sys.path.append(str(PurePath(__file__).parents[1]))

from functions import Copy


def _recursive_property(copyobj: Copy, **kwargs) -> Copy:
    """
    Recursively sets specified properties in `Copy` object
    """
    if not kwargs:
        warn(f"kwargs is empty")
    elif "children" in kwargs:
        raise ValueError

    children: Sequence[Copy] = tuple(
        _recursive_property(child, **kwargs) for child in copyobj.children
    )
    return utils.replace_namedtuple(copyobj, children=children, **kwargs)


def _recursive_replace(copyobj: Copy, f: Callable[[Copy], Copy]) -> Copy:
    """
    Recursively transforms each `Copy` object through provided unary function
    """
    children: Sequence[Copy] = tuple(
        _recursive_replace(child, f) for child in copyobj.children
    )
    return utils.replace_namedtuple(f(copyobj), children=children)


def _recursive_replace_subdir(
    copyobj: Copy, parent_dir: Optional[Path] = None, suffix: str = "~"
) -> Copy:
    children: Sequence[Copy] = tuple(
        _recursive_replace_subdir(child, copyobj.path, suffix)
        for child in copyobj.children
    )
    if parent_dir is None:
        return utils.replace_namedtuple(
            copyobj, subdir=copyobj.path.name + suffix, children=children
        )

    return utils.replace_namedtuple(
        copyobj,
        subdir=copyobj.path.relative_to(parent_dir).with_name(
            copyobj.path.name + suffix
        ),
        children=children,
    )


def test_copy_simple_artificial(root_copyobj):
    assert not root_copyobj.artificial()

    diff_initial_subdir = utils.replace_namedtuple(root_copyobj, subdir=PurePath("a"))
    assert not diff_initial_subdir.artificial()

    diff_file_permissions = utils.replace_namedtuple(root_copyobj, default_file_perms="000")
    assert diff_file_permissions.artificial()

    diff_dir_permissions = utils.replace_namedtuple(root_copyobj, default_dir_perms="000")
    assert diff_dir_permissions.artificial() == diff_dir_permissions.path.is_dir()


def test_copy_recursive_artificial(copyobj_filled_children):
    assert not copyobj_filled_children.artificial()
    if copyobj_filled_children.children:
        diff_subdir = _recursive_replace_subdir(copyobj_filled_children)
        assert diff_subdir.artificial()
        assert utils.replace_namedtuple(diff_subdir, subdir=None).artificial()


# functions that serve as edge cases and will be used by `_recursive_replace`


class CopyMetadataModifiers:
    def set_same_user_owner(copyobj: Copy) -> Copy:
        return utils.replace_namedtuple(
            copyobj, default_user_owner=copyobj.path.stat().st_uid
        )

    def set_same_user_owner_str(copyobj: Copy) -> Copy:
        return utils.replace_namedtuple(
            copyobj,
            default_user_owner=pwd.getpwuid(copyobj.path.stat().st_uid).pw_name,
        )

    def set_same_group_owner(copyobj: Copy) -> Copy:
        return utils.replace_namedtuple(
            copyobj, default_group_owner=copyobj.path.stat().st_gid
        )

    def set_same_group_owner_str(copyobj: Copy) -> Copy:
        return utils.replace_namedtuple(
            copyobj,
            default_group_owner=grp.getgrgid(copyobj.path.stat().st_gid).gr_name,
        )

    def set_diff_user_owner(copyobj: Copy) -> Copy:
        return utils.replace_namedtuple(
            copyobj, default_user_owner=copyobj.path.stat().st_uid + 1
        )

    def set_diff_user_owner_str(copyobj: Copy) -> Copy:
        copyobj_uid: int = copyobj.path.stat().st_uid
        for pw in pwd.getpwall():
            if pw.pw_uid != copyobj_uid:
                return utils.replace_namedtuple(copyobj, default_user_owner=pw.pw_name)

    def set_diff_group_owner(copyobj: Copy) -> Copy:
        return utils.replace_namedtuple(
            copyobj, default_group_owner=copyobj.path.stat().st_gid + 1
        )

    def set_diff_group_owner_str(copyobj: Copy) -> Copy:
        copyobj_gid: int = copyobj.path.stat().st_gid
        for gr in grp.getgrall():
            if gr.gr_gid != copyobj_gid:
                return utils.replace_namedtuple(copyobj, default_user_owner=gr.gr_name)

    def set_random_file_perms(copyobj: Copy) -> Copy:
        return utils.replace_namedtuple(
            copyobj, default_file_perms=f"{random.randrange(0o1000):03o}"
        )

    def set_random_dir_perms(copyobj: Copy) -> Copy:
        return utils.replace_namedtuple(
            copyobj, default_file_perms=f"{random.randrange(0o1000):03o}"
        )


@pytest.mark.parametrize(
    "property_changer,artificial",
    ChainMap(
        {
            method: re.search(
                r"(?:^|[^a-z0-9])(same)(?:$|[^a-z0-9])", method_name, re.I
            )
            is None
            for method_name, method in vars(CopyMetadataModifiers).items()
            if not method_name.startswith("_")
        },
        {CopyMetadataModifiers.set_random_dir_perms: (lambda x: x.path.is_dir())},
    ).items(),
)
def test_copy_recursive_property_artificial(
    copyobj_filled_children,
    property_changer: Callable[[Copy], Copy],
    artificial: Union[bool, Callable[[Copy], bool]],
):
    replaced: Copy = _recursive_replace(copyobj_filled_children, property_changer)
    if callable(artificial):
        artificial = artificial(replaced)
    assert replaced.artificial() == artificial
    if copyobj_filled_children.children:
        assert (
            utils.replace_namedtuple(
                copyobj_filled_children, children=replaced.children
            ).artificial()
            == artificial
        )


def test_copy_custom_subdir_set_metadata(copyobj_filled_children, tmp_path):
    # We are only testing custom subdir properties
    utils.copy_to(copyobj_filled_children, tmp_path)

    custom_subdirs: Copy = utils.replace_namedtuple(
        _recursive_replace_subdir(copyobj_filled_children), subdir=None
    )
    custom_subdirs.set_metadata(tmp_path)

    # https://stackoverflow.com/a/6681395

    org_root_path: Path = custom_subdirs.path.relative_to(
        Path(__file__).parent / "data"
    )
    utils.equal_trees(
        tmp_path, Path(__file__).parent / "custom_subdirs" / org_root_path
    )
