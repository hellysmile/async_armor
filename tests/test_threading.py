import asyncio
from concurrent.futures import ThreadPoolExecutor

from async_armor import ArmorMeta, armor

SLEEP = 0.1


def thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    c = 0

    @asyncio.coroutine
    def coro():
        nonlocal c
        yield from asyncio.sleep(SLEEP)
        c = 1

    assert len(ArmorMeta.objects) == 0

    task = armor(coro())

    assert len(ArmorMeta.objects) == 1

    task.cancel()

    armor.close()
    loop.run_until_complete(armor.wait_closed())

    assert len(ArmorMeta.objects) == 1

    del task

    assert len(ArmorMeta.objects) == 0

    return c


def test_threading():
    n = 10

    futs = []

    with ThreadPoolExecutor(max_workers=n) as executor:
        for _ in range(n):
            futs.append(executor.submit(thread))

    for fut in futs:
        assert fut.result() == 1
