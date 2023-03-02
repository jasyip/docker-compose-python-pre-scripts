import sys
from pathlib import Path, PurePath
from shutil import copytree, rmtree

import pytest

sys.path.append(str(PurePath(__file__).parents[1]))

import functions


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
