from collections.abc import Sequence
from itertools import accumulate, combinations, tee
from math import ceil
from pathlib import PurePath

import pytest

import utils

from functions import Copy, _VolDir


def sorted_partitions(n, bins, *, upper_bound=None):
    if bins == 1:
        yield (0, n)
        return

    if upper_bound is None:
        upper_bound = n
    for i in range(ceil(n / bins), upper_bound + 1):
        for rest in sorted_partitions(n - i, bins - 1, upper_bound=i):
            yield rest + (i,)


# https://docs.python.org/3/library/itertools.html#itertools.pairwise
def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


_combination_lens = frozenset(range(1, len(utils.DATA_DIRS) + 1)) - frozenset(
    range(3, len(utils.DATA_DIRS) - 1)
)


def combination_mappings(items, lens, max_partitions):
    if not isinstance(items, Sequence):
        items = tuple(items)
    if isinstance(lens, int):
        lens = range(1, lens + 1)
    for subset_len in lens:
        for num_volumes in range(1, min(subset_len, max_partitions) + 1):
            for partitions in sorted_partitions(subset_len, num_volumes):
                for powerset in combinations(items, subset_len):
                    yield tuple(
                        powerset[slice(*b)] for b in pairwise(accumulate(partitions))
                    )


@pytest.fixture(
    scope="module",
    params=combination_mappings(range(len(utils.DATA_DIRS)), _combination_lens, 2),
)
def vol_test_data_map(request):
    return request.param


@pytest.fixture(scope="module")
def vol_root_copyobj_map(vol_test_data_map):
    return {
        str(name): frozenset(Copy(utils.DATA_DIRS[i]) for i in pw)
        for name, pw in enumerate(vol_test_data_map, 1)
    }


@pytest.fixture(scope="module")
def vol_copyobj_filled_children_map(vol_test_data_map):
    return {
        str(name): frozenset(
            utils.filled_children(Copy(utils.DATA_DIRS[i])) for i in pw
        )
        for name, pw in enumerate(vol_test_data_map, 1)
    }


def test_get_vol_dirs(vol_root_copyobj_map):
    vol_dirs = _VolDir.get_dirs(vol_root_copyobj_map)
    assert len(vol_dirs) == sum(map(bool, vol_root_copyobj_map.values()))


def test_get_vol_dirs2(vol_copyobj_filled_children_map):
    vol_dirs = _VolDir.get_dirs(vol_copyobj_filled_children_map)
    assert len(vol_dirs) == sum(map(bool, vol_copyobj_filled_children_map.values()))
