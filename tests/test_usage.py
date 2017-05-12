import asyncio

import pytest

from async_armor import armor

SLEEP_MORE = 0.1
SLEEP_LESS = 0.05


@pytest.mark.run_loop
@asyncio.coroutine
def test_deco_cls_kwargs_loop(loop):
    asyncio.set_event_loop(loop)

    @armor(cls=True, kwargs=True, loop='loop')
    @asyncio.coroutine
    def coro():
        pass

    with pytest.raises(AssertionError):
        yield from coro()

    armor.close()
    yield from armor.wait_closed()


@pytest.mark.run_loop
@asyncio.coroutine
def test_shield_cls_kwargs_loop(loop):
    asyncio.set_event_loop(loop)

    @asyncio.coroutine
    def coro():
        pass

    obj = coro()

    with pytest.raises(AssertionError):
        yield from armor(obj, cls=True, kwargs=True)

    yield from obj

    armor.close()
    yield from armor.wait_closed()


@pytest.mark.run_loop
@asyncio.coroutine
def test_deco_closed(loop):
    asyncio.set_event_loop(loop)

    @armor
    @asyncio.coroutine
    def coro():
        pass

    armor.close()

    with pytest.raises(RuntimeError):
        yield from coro()

    yield from armor.wait_closed()

    with pytest.raises(RuntimeError):
        yield from coro()


@pytest.mark.run_loop
@asyncio.coroutine
def test_deco_closing(loop):
    asyncio.set_event_loop(loop)

    @armor
    @asyncio.coroutine
    def coro():
        pass

    armor.close()

    with pytest.raises(AssertionError):
        armor.close()

    with pytest.raises(AssertionError):
        coro.close()

    yield from armor.wait_closed()

    with pytest.raises(AssertionError):
        yield from coro.wait_closed()


@pytest.mark.run_loop
@asyncio.coroutine
def test_deco_reload(loop):
    asyncio.set_event_loop(loop)

    @armor
    @asyncio.coroutine
    def coro():
        pass

    armor.close()
    yield from armor.wait_closed()

    armor.reload()

    yield from coro()

    armor.close()
    yield from armor.wait_closed()
