from shutil import copytree, rmtree
from tempfile import mkdtemp
from pathlib import Path, PurePath
import sys

sys.path.append(str(PurePath(__file__).parents[1]))
import functions

import pytest

parametrize = pytest.mark.parametrize

data_dir = Path(__file__).parent / "data"


@parametrize(
    "directory",
    (
        "many_files",
        "many_files_tree",
        "no_files",
        "no_file_tree",
        "single_file",
        "single_file_tree",
    ),
)
def test_shred_dir(directory):
    directory = data_dir / directory
    tmp_dir = Path(mkdtemp())

    copytree(directory, tmp_dir / directory.name)

    try:
        functions.shred_dir(tmp_dir)
        assert not tmp_dir.is_dir()
    except:
        rmtree(tmp_dir)
        raise
