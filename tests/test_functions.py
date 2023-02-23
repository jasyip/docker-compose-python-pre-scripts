import os
import sys
from collections.abc import Callable
from pathlib import Path, PurePath
from shutil import copytree, rmtree
from typing import Any, Optional

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
    dest_path = tmp_path / test_data_path.name
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


def filled_children(copyobj, *args, **kwargs):
    if not copyobj.path.is_dir():
        return copyobj

    children = map(
        filled_children,
        (Copy(path, *args, **kwargs) for path in copyobj.path.iterdir()),
    )
    return copyobj._replace(children=tuple(children))

def recursive_property(copyobj, **kwargs):
    if "children" in kwargs:
        raise ValueError

    children = tuple(recursive_property(child, *args, **kwargs) for child in copyobj.children)
    return copyobj._replace(children=children, **kwargs)


def test_copy_artificial(root_copyobj):
    assert not root_copyobj.artificial()

    with_children = filled_children(root_copyobj)
    assert not with_children.artificial()

    diff_initial_subdir = root_copyobj._replace(subdir = PurePath("/a"))
    assert not diff_initial_subdir.artificial()





"""
@parametrize("copyobj", ())
def test_set_metadata(copyobj):

@parametrize("volume_name, directories", ())
def test_copy_to_volume(volume_name, directories):
"""
