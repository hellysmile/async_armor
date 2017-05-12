from functools import partial

from async_armor import unpartial


def test_unpartial():
    def fn():
        pass

    obj = partial(partial(fn))

    assert unpartial(obj).__name__ == 'fn'
