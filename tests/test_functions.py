import grp
import inspect
import os
import pwd
import sys
from collections.abc import Callable, Sequence
from inspect import Parameter
from pathlib import Path, PurePath
from shutil import copytree, rmtree
from typing import Any, Optional, NamedTuple
from warnings import warn

import pytest

sys.path.append(str(PurePath(__file__).parents[1]))

import functions
from functions import Copy


@pytest.fixture(params=(Path(__file__).parent / "data").iterdir())
def test_data_path(request):
    return request.param


def test_shred_dir(test_data_path, tmp_path):
    if not test_data_path.is_dir():
        pytest.skip(f"{test_data_path=} is not a directory")
    dest_path: Path = tmp_path / test_data_path.name
    copytree(test_data_path, dest_path)

    try:
        functions.shred_dir(dest_path)
        assert not dest_path.exists()
    except:
        rmtree(dest_path)
        raise


@pytest.fixture
def root_copyobj(test_data_path):
    return Copy(test_data_path)


def replace_namedtuple(nt: NamedTuple, **kwargs) -> NamedTuple:
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


@pytest.fixture
def copyobj_filled_children(root_copyobj):
    def filled_children(copyobj, *args, **kwargs):
        if not copyobj.path.is_dir():
            if copyobj is root_copyobj:
                pytest.skip(f"{copyobj} is just a simple file")
            return copyobj

        children: Sequence[Copy] = tuple(
            map(
                filled_children,
                (Copy(path, *args, **kwargs) for path in copyobj.path.iterdir()),
            )
        )
        return replace_namedtuple(copyobj, children=children)

    return filled_children(root_copyobj)


def recursive_property(copyobj, **kwargs):
    if not kwargs:
        warn(f"kwargs is empty")
    elif "children" in kwargs:
        raise ValueError

    children: Sequence[Copy] = tuple(
        recursive_property(child, **kwargs) for child in copyobj.children
    )
    return replace_namedtuple(copyobj, children=children, **kwargs)


def recursive_replace(copyobj, f):
    children: Sequence[Copy] = tuple(
        recursive_replace(child, f) for child in copyobj.children
    )
    return replace_namedtuple(f(copyobj), children=children)


def recursive_replace_subdir(copyobj, parent_dir=None, suffix="~"):
    children: Sequence[Copy] = tuple(
        recursive_replace_subdir(child, copyobj.path, suffix)
        for child in copyobj.children
    )
    if parent_dir is None:
        return replace_namedtuple(
            copyobj, subdir=copyobj.path.name + suffix, children=children
        )

    return replace_namedtuple(
        copyobj,
        subdir=copyobj.path.relative_to(parent_dir).with_name(
            copyobj.path.name + suffix
        ),
        children=children,
    )


def test_copy_simple_artificial(root_copyobj):
    assert not root_copyobj.artificial()

    diff_initial_subdir = replace_namedtuple(root_copyobj, subdir=PurePath("a"))
    assert not diff_initial_subdir.artificial()

    diff_file_permissions = replace_namedtuple(root_copyobj, default_file_perms="000")
    assert diff_file_permissions.artificial()

    diff_dir_permissions = replace_namedtuple(root_copyobj, default_dir_perms="000")
    assert diff_dir_permissions.artificial() == diff_dir_permissions.path.is_dir()


def test_copy_recursive_artificial(copyobj_filled_children):
    assert not copyobj_filled_children.artificial()
    if copyobj_filled_children.children:
        diff_subdir = recursive_replace_subdir(copyobj_filled_children)
        assert diff_subdir.artificial()


def set_same_user_owner(copyobj):
    return replace_namedtuple(copyobj, default_user_owner=copyobj.path.stat().st_uid)


def set_same_user_owner_str(copyobj):
    return replace_namedtuple(
        copyobj, default_user_owner=pwd.getpwuid(copyobj.path.stat().st_uid).pw_name
    )


def set_same_group_owner(copyobj):
    return replace_namedtuple(copyobj, default_group_owner=copyobj.path.stat().st_gid)


def set_same_group_owner_str(copyobj):
    return replace_namedtuple(
        copyobj, default_group_owner=grp.getgrgid(copyobj.path.stat().st_gid).gr_name
    )


def set_diff_user_owner(copyobj):
    return replace_namedtuple(
        copyobj, default_user_owner=copyobj.path.stat().st_uid + 1
    )


def set_diff_user_owner_str(copyobj):
    copyobj_uid = copyobj.path.stat().st_uid
    for pw in pwd.getpwall():
        if pw.pw_uid != copyobj_uid:
            return replace_namedtuple(copyobj, default_user_owner=pw.pw_name)


def set_diff_group_owner(copyobj):
    return replace_namedtuple(
        copyobj, default_group_owner=copyobj.path.stat().st_gid + 1
    )


def set_diff_group_owner_str(copyobj):
    copyobj_gid = copyobj.path.stat().st_gid
    for gr in grp.getgrall():
        if gr.gr_gid != copyobj_gid:
            return replace_namedtuple(copyobj, default_user_owner=gr.gr_name)


@pytest.mark.parametrize(
    "property_changer,artificial",
    (
        (set_same_user_owner, False),
        (set_same_user_owner_str, False),
        (set_same_group_owner, False),
        (set_same_group_owner_str, False),
        (set_diff_user_owner, True),
        (set_diff_user_owner_str, True),
        (set_diff_group_owner, True),
        (set_diff_group_owner_str, True),
    ),
)
def test_copy_recursive_property_artificial(
    copyobj_filled_children, property_changer, artificial
):
    replaced = recursive_replace(copyobj_filled_children, property_changer)
    assert replaced.artificial() == artificial
    if copyobj_filled_children.children:
        assert (
            replace_namedtuple(
                copyobj_filled_children, children=replaced.children
            ).artificial()
            == artificial
        )


"""
@parametrize("copyobj", ())
def test_set_metadata(copyobj):

@parametrize("volume_name, directories", ())
def test_copy_to_volume(volume_name, directories):
"""
