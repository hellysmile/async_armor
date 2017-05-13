import sys

import asyncio
from functools import partial

import pytest

from async_armor import armor

SLEEP = 0.1


@pytest.mark.run_loop
@asyncio.coroutine
def test_default_loop(loop):
    asyncio.set_event_loop(loop)

    c = 0

    @armor
    @asyncio.coroutine
    def coro():
        nonlocal c
        yield from asyncio.sleep(SLEEP)
        c = 1

    task = asyncio.ensure_future(coro())
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
        yield from asyncio.sleep(SLEEP, loop=loop)
        c = 1

    task = asyncio.ensure_future(coro(), loop=loop)
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
        yield from asyncio.sleep(SLEEP, loop=_loop)
        c = 1

    task = asyncio.ensure_future(coro(_loop=loop), loop=loop)
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
            yield from asyncio.sleep(SLEEP, loop=self._loop)
            c = 1

    task = asyncio.ensure_future(Obj(loop=loop).coro(), loop=loop)
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
            yield from asyncio.sleep(SLEEP, loop=self._loop)
            c = 1

    task = asyncio.ensure_future(Obj(loop=loop).coro(), loop=loop)
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
                yield from asyncio.sleep(SLEEP, loop=self._loop)
                c = 1

            coro = partialmethod(_coro)

        task = asyncio.ensure_future(Obj(loop=loop).coro(), loop=loop)
        task.cancel()

        armor.close()
        yield from armor.wait_closed(loop=loop)

        assert c == 1
