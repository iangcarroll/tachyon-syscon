"""Partition collected tests without maintaining duplicate CI case lists."""
import pytest


def parse_shard(value):
    try:
        index, count = map(int, value.split('/'))
        if not 0 <= index < count:
            raise ValueError
    except (ValueError, TypeError):
        raise pytest.UsageError('--test-shard must be INDEX/COUNT with 0 <= INDEX < COUNT') from None
    return index, count


def pytest_addoption(parser):
    parser.addoption('--test-shard', type=parse_shard, default=None,
                     help='Run a zero-based INDEX/COUNT partition of collected tests')


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    shard = config.getoption('test_shard')
    if shard is None:
        return
    index, count = shard
    selected, deselected = [], []
    for position, item in enumerate(sorted(items, key=lambda item: item.nodeid)):
        (selected if position % count == index else deselected).append(item)
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected
