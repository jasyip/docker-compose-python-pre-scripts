import sys
from pathlib import Path, PurePath
from typing import Final

import pytest
import utils

sys.path.append(str(PurePath(__file__).parents[1]))

from functions import Copy


@pytest.fixture(scope="module", params=utils.DATA_DIRS)
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

    if not root_copyobj.path.is_dir():
        pytest.skip(f"{root_copyobj} is just a simple file")

    return utils.filled_children(root_copyobj)
