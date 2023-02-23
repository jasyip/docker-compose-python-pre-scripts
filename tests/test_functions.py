from shutil import copytree, rmtree
from tempfile import mkdtemp
from pathlib import Path, PurePath
import sys

sys.path.append(str(PurePath(__file__).parents[1]))
import functions
from functions import Copy

import os
import pytest


@pytest.fixture(params=(Path(__file__).parent / "data").iterdir())
def data_dir(request):
    return request.param


def test_shred_dir(data_dir):
    tmp_dir = Path(mkdtemp())

    copytree(data_dir, tmp_dir / data_dir.name)

    try:
        functions.shred_dir(tmp_dir)
        assert not tmp_dir.is_dir()
    except:
        rmtree(tmp_dir)
        raise





@pytest.fixture
def root_copyobj(data_dir):
    return Copy(data_dir)



def filled_children(copyobj, *args, **kwargs):

    if not copyobj.path.is_dir():
        return copyobj

    children = map(filled_children, (Copy(path, *args, **kwargs) for path in copyobj.path.iterdir()))
    return copyobj._replace(children=tuple(children))


def test_copy_artificial(root_copyobj):
    assert not root_copyobj.artificial()

    with_children = filled_children(root_copyobj)
    assert not with_children.artificial()

"""
@parametrize("copyobj", ())
def test_set_metadata(copyobj):

@parametrize("volume_name, directories", ())
def test_copy_to_volume(volume_name, directories):
"""
