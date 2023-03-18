from itertools import chain, combinations
from pathlib import PurePath

import pytest

import utils


_combination_lens = frozenset(range(1, len(utils.DATA_DIRS) + 1)) - frozenset(range(3, len(utils.DATA_DIRS) - 1))

@pytest.mark.parametrize("data_path_powerset", map(frozenset, chain.from_iterable(combinations(utils.DATA_DIRS, r) for r in _combination_lens)))
def test_get_vol_dirs(data_path_powerset):
    pass
    # print(data_path_powerset)
