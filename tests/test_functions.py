import sys
from pathlib import PurePath

import pytest

sys.path.append(str(PurePath(__file__).parents[1]))

from functions import _VolDir, copy_to_volume

"""
def test_get_vol_dirs():
    pass
"""
