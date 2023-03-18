from copy import deepcopy
from itertools import combinations, tee
from pathlib import PurePath

import pytest

import utils

from functions import Copy, _VolDir

# https://docs.python.org/3/library/itertools.html#itertools.combinations_with_replacement
def combinations_with_replacement(iterable, r):
    # combinations_with_replacement('ABC', 2) --> AA AB AC BB BC CC
    pool = tuple(iterable)
    n = len(pool)
    if not n:
        return
    if not r:
        yield tuple()
        return
    indices = [0] * r
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != n - 1:
                break
        else:
            return
        indices[i:] = [indices[i] + 1] * (r - i)
        yield tuple(pool[i] for i in indices)

# https://docs.python.org/3/library/itertools.html#itertools.pairwise
def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


_combination_lens = frozenset(range(1, len(utils.DATA_DIRS) + 1)) - frozenset(range(3, len(utils.DATA_DIRS) - 1))

def volume_mappings():
    for num_dirs in _combination_lens:
        for num_volumes in range(1, min(num_dirs, 2) + 1):
            for inds in combinations_with_replacement(range(num_dirs), num_volumes - 1):
                inds = (0,) + inds + (num_dirs,)
                for powerset in combinations(map(Copy, utils.DATA_DIRS), num_dirs):
                    to_yield = {}
                    for vol_name_id, range_bounds in enumerate(pairwise(inds), 1):
                        to_yield[str(vol_name_id)] = frozenset(powerset[slice(*range_bounds)])
                    yield to_yield

@pytest.mark.parametrize("test_data_volume_mappings", volume_mappings())
def test_get_vol_dirs(test_data_volume_mappings):
    vol_dirs = _VolDir.get_dirs(test_data_volume_mappings)
    assert len(vol_dirs) == sum(map(bool, test_data_volume_mappings.values()))
