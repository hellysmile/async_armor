import sys

import asyncio
from functools import partial

import pytest

from async_armor import armor, create_task

SLEEP_MORE = 0.1
SLEEP_LESS = 0.05


@pytest.mark.run_loop
@asyncio.coroutine
def test_default_loop(loop):
    asyncio.set_event_loop(loop)

    c = 0

    @armor
    @asyncio.coroutine
    def coro():
        nonlocal c
        yield from asyncio.sleep(SLEEP_MORE)
        c = 1

    @asyncio.coroutine
    def inner():
        yield from coro()

    task = create_task()(inner())
    yield from asyncio.sleep(SLEEP_LESS)
    task.cancel()

    armor.close()
    yield from armor.wait_closed()

    assert c == 1


@pytest.mark.run_loop
@asyncio.coroutine
def test_explicit_loop(loop):
    c = 0

    @armor(loop=loop)
    @asyncio.coroutine
    def coro():
        nonlocal c
        yield from asyncio.sleep(SLEEP_MORE, loop=loop)
        c = 1

    @asyncio.coroutine
    def inner():
        yield from coro()

    task = create_task(loop=loop)(inner())
    yield from asyncio.sleep(SLEEP_LESS, loop=loop)
    task.cancel()

    armor.close()
    yield from armor.wait_closed(loop=loop)

    assert c == 1


@pytest.mark.run_loop
@asyncio.coroutine
def test_kwargs_loop(loop):
    c = 0

    @armor(kwargs=True, loop='_loop')
    @asyncio.coroutine
    def coro(*, _loop):
        nonlocal c
        yield from asyncio.sleep(SLEEP_MORE, loop=_loop)
        c = 1

    @asyncio.coroutine
    def inner():
        yield from coro(_loop=loop)

    task = create_task(loop=loop)(inner())
    yield from asyncio.sleep(SLEEP_LESS, loop=loop)
    task.cancel()

    armor.close()
    yield from armor.wait_closed(loop=loop)

    assert c == 1


@pytest.mark.run_loop
@asyncio.coroutine
def test_cls_loop(loop):
    c = 0

    class Obj:
        def __init__(self, *, loop):
            self._loop = loop

        @armor(cls=True, loop='_loop')
        @asyncio.coroutine
        def coro(self):
            nonlocal c
            yield from asyncio.sleep(SLEEP_MORE, loop=self._loop)
            c = 1

    @asyncio.coroutine
    def inner():
        yield from Obj(loop=loop).coro()

    task = create_task(loop=loop)(inner())
    yield from asyncio.sleep(SLEEP_LESS, loop=loop)
    task.cancel()

    armor.close()
    yield from armor.wait_closed(loop=loop)

    assert c == 1


@pytest.mark.run_loop
@asyncio.coroutine
def test_deco_cls_partial_loop(loop):
    c = 0

    class Obj:
        def __init__(self, *, loop):
            self._loop = loop
            self.coro = partial(self._coro)

        @armor(cls=True, loop='_loop')
        @asyncio.coroutine
        def _coro(self):
            nonlocal c
            yield from asyncio.sleep(SLEEP_MORE, loop=self._loop)
            c = 1

    @asyncio.coroutine
    def inner():
        yield from Obj(loop=loop).coro()

    task = create_task(loop=loop)(inner())
    yield from asyncio.sleep(SLEEP_LESS, loop=loop)
    task.cancel()

    armor.close()
    yield from armor.wait_closed(loop=loop)

    assert c == 1


if sys.version_info >= (3, 4, 0):
    from functools import partialmethod

    @pytest.mark.run_loop
    @asyncio.coroutine
    def test_deco_cls_partialmethod_loop(loop):
        c = 0

        class Obj:
            def __init__(self, *, loop):
                self._loop = loop

            @armor(cls=True, loop='_loop')
            @asyncio.coroutine
            def _coro(self):
                nonlocal c
                yield from asyncio.sleep(SLEEP_MORE, loop=self._loop)
                c = 1

            coro = partialmethod(_coro)

        @asyncio.coroutine
        def inner():
            yield from Obj(loop=loop).coro()

        task = create_task(loop=loop)(inner())
        yield from asyncio.sleep(SLEEP_LESS, loop=loop)
        task.cancel()

        armor.close()
        yield from armor.wait_closed(loop=loop)

        assert c == 1
