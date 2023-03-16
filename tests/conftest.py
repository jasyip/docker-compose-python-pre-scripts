import sys
from collections.abc import Sequence
from pathlib import Path, PurePath

import pytest

import utils

sys.path.append(str(PurePath(__file__).parents[1]))

from functions import Copy


@pytest.fixture(scope="module", params=(Path(__file__).parent / "data").iterdir())
def test_data_path(request):
    """
    Return all data test cases under the "data" folder
    """
    return request.param


@pytest.fixture(scope="module")
def root_copyobj(test_data_path):
    return Copy(test_data_path)


@pytest.fixture(scope="module")
def copyobj_filled_children(root_copyobj):
    """
    Returns a `Copy` object whose children are also recursively-filled `Copy` objects that
    accurately reflect the file tree structure
    """

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
        return utils.replace_namedtuple(copyobj, children=children)

    return filled_children(root_copyobj)
