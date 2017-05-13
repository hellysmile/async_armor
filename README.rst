async_armor
===========

:info: Graceful drop-in replacement for asyncio.shield

.. image:: https://img.shields.io/travis/wikibusiness/async_armor.svg
    :target: https://travis-ci.org/wikibusiness/async_armor

.. image:: https://img.shields.io/pypi/v/async_armor.svg
    :target: https://pypi.python.org/pypi/async_armor

Installation
------------

.. code-block:: shell

    pip install async_armor

Usage
-----

.. code-block:: python

    import asyncio

    from async_armor import armor

    calls = 0

    async def call_shield():
        global calls
        await asyncio.sleep(1)
        calls += 1

    @armor
    async def call_deco():
        global calls
        await asyncio.sleep(1)
        calls += 1

    async def main():
        task = armor(call_shield())
        task.cancel()

        task = asyncio.ensure_future(call_deco())
        task.cancel()

    loop = asyncio.get_event_loop()

    loop.run_until_complete(main())

    armor.close()
    loop.run_until_complete(armor.wait_closed())

    assert calls == 2

    loop.close()


Python 3.3+ is required
