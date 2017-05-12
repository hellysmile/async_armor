import asyncio
from functools import partial

import pytest

from async_armor import armor, create_task


SLEEP_MORE = 0.1
SLEEP_LESS = 0.05


@pytest.mark.run_loop
@asyncio.coroutine
def test_shield(loop):
    asyncio.set_event_loop(loop)

    c = 0

    @asyncio.coroutine
    def coro():
        nonlocal c
        yield from asyncio.sleep(SLEEP_MORE)
        c = 1

    task = armor(coro())
    task.cancel()

    armor.close()
    yield from armor.wait_closed()

    assert c == 1


@pytest.mark.run_loop
@asyncio.coroutine
def test_shield_many(loop):
    asyncio.set_event_loop(loop)

    c = 0
    n = 100

    @asyncio.coroutine
    def coro():
        nonlocal c
        yield from asyncio.sleep(SLEEP_MORE)
        c += 1

    coros = []

    for _ in range(n):
        coros.append(armor(coro()))

    task = asyncio.gather(*coros)
    task.cancel()

    armor.close()
    yield from armor.wait_closed()

    assert c == n


@pytest.mark.run_loop
@asyncio.coroutine
def test_deco(loop):
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
def test_deco_call(loop):
    asyncio.set_event_loop(loop)

    c = 0

    @armor()
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
def test_deco_close(loop):
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

    coro.close()
    yield from coro.wait_closed()

    assert c == 1


@pytest.mark.run_loop
@asyncio.coroutine
def test_deco_partial(loop):
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
        yield from partial(coro)()

    task = create_task()(inner())
    yield from asyncio.sleep(SLEEP_LESS)
    task.cancel()

    armor.close()
    yield from armor.wait_closed()

    assert c == 1
