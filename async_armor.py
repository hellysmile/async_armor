import asyncio  # noqa # isort:skip
import logging
import warnings
import weakref
from functools import wraps
from operator import itemgetter
from threading import local

try:
    from asyncio import ensure_future
except ImportError:
    ensure_future = getattr(asyncio, 'async')


logger = logging.getLogger(__name__)

__version__ = '0.0.2'

_locals = local()

not_set = ...


def unpartial(fn):
    while hasattr(fn, 'func'):
        fn = fn.func

    return fn


def create_future(*, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    try:
        return loop.create_future()
    except AttributeError:
        return asyncio.Future(loop=loop)


class staticproperty(property):  # noqa
    def __get__(self, cls, owner):
        return staticmethod(self.fget).__get__(owner)()


class ArmorMeta(type):

    def __call__(self, *args, **kwargs):
        obj = super().__call__(*args, **kwargs)

        ArmorMeta.objects.add(obj)

        return obj

    @staticproperty
    def objects():
        objects = getattr(_locals, 'objects', None)

        if objects is None:
            _locals.objects = weakref.WeakSet()

        return _locals.objects

    @staticmethod
    def reload():
        for obj in ArmorMeta.objects:
            assert obj.closed, 'Cannot reload while not closed'

            obj._closing = False
            obj._closed = False

    @staticmethod
    def close():
        for obj in ArmorMeta.objects:
            if obj.decorated and not obj.closed:
                obj.close()

    @staticmethod
    @asyncio.coroutine
    def wait_closed(*, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        objs = []
        coros = []

        for obj in ArmorMeta.objects:
            if obj.armored is None or obj.closed:
                continue

            objs.append(obj.armored)
            coros.append(obj.wait_closed(loop=loop))

        if not objs:
            return {}

        _ret = yield from asyncio.gather(*coros, loop=loop)

        return dict(filter(itemgetter(1), zip(objs, _ret)))


class Armor(metaclass=ArmorMeta):

    def __init__(self, cls=not_set, kwargs=not_set, *, loop=not_set):
        self.cls = cls
        self.kwargs = kwargs
        self.loop = loop

        self._futures = set()
        self._closing = False
        self._closed = False

        self.__armored = None

        self.__decorated = False

    @property
    def armored(self):
        return self.__armored

    @property
    def closed(self):
        return self._closed

    @property
    def decorated(self):
        return self.__decorated

    def __del__(self):
        if self.__armored is None:
            return

        if not self._closed:
            msg = 'Unclosed armor: {armor}'.format(
                armor=self.__armored,
            )

            logger.error(msg)

            warnings.simplefilter('once', ResourceWarning)

            warnings.warn(msg, ResourceWarning, stacklevel=2)

    def _armor(self, inner, *, loop):
        # copy paste shield from asyncio
        # https://github.com/python/cpython/blob/master/Lib/asyncio/tasks.py#L638  # noqa

        self._futures.add(inner)

        inner.add_done_callback(self._futures.remove)

        if inner.done():
            # Shortcut.
            return inner

        outer = create_future(loop=loop)

        def _done_callback(inner):
            if outer.cancelled():
                if not inner.cancelled():
                    # Mark inner's result as retrieved.
                    inner.exception()

                return

            if inner.cancelled():
                outer.cancel()
            else:
                exc = inner.exception()

                if exc is not None:
                    outer.set_exception(exc)
                else:
                    outer.set_result(inner.result())

        inner.add_done_callback(_done_callback)

        return outer

    def armor(self, arg, *, loop=None):
        assert self.__armored is None, 'armor {armor} already applied'.format(
            armor=self,
        )

        if loop is None:
            loop = asyncio.get_event_loop()

        inner = ensure_future(arg, loop=loop)

        inner.add_done_callback(self._close_armor)

        outer = self._armor(inner, loop=loop)

        outer.wait_closed = self.wait_closed

        self.__armored = arg

        return outer

    def armor_decorator(self, fn):
        assert self.cls is not not_set
        assert self.kwargs is not not_set
        assert self.loop is not not_set

        assert self.__armored is None, 'armor {armor} already applied'.format(
            armor=self,
        )

        @wraps(fn)
        def decorator(*args, **kwargs):
            if self._closing:
                raise RuntimeError('armor is closing')

            if isinstance(self.loop, str):
                assert self.cls ^ self.kwargs, 'choose self.loop or kwargs["loop"]'  # noqa

                if self.cls:
                    _self = getattr(unpartial(fn), '__self__', None)

                    if _self is None:
                        assert args, 'seems not unbound function'
                        _self = args[0]

                    _loop = getattr(_self, self.loop)
                elif self.kwargs:
                    _loop = kwargs[self.loop]
            elif self.loop is None:
                _loop = asyncio.get_event_loop()
            else:
                _loop = self.loop

            coro = fn(*args, **kwargs)

            inner = ensure_future(coro, loop=_loop)

            return self._armor(inner, loop=_loop)

        decorator.close = self.close
        decorator.wait_closed = self.wait_closed

        self.__armored = decorator

        self.__decorated = True

        return decorator

    def _close_armor(self, inner):
        assert not self.__decorated, 'used as decorator'

        self._closed = True

    def close(self):
        assert self.__decorated, 'not used as decorator'
        assert not self._closing, 'already closing'

        self._closing = True

    @asyncio.coroutine
    def wait_closed(self, *, loop=None):
        if self.__decorated:
            assert self._closing, 'not closing yet'
        assert not self._closed, 'already closed'

        if loop is None:
            loop = asyncio.get_event_loop()

        if (
            self.__armored is None or
            not self._futures
        ):
            ret = []
        else:
            ret = yield from asyncio.gather(*self._futures, loop=loop)

        self._closed = True

        assert not self._futures, 'zombie futures detected'

        if not self.__decorated:
            return ret[0] if ret else None
        else:
            return ret


def armor(fn=None, *, cls=False, kwargs=False, loop=None):
    def wrapper(fn):
        return Armor(cls=cls, kwargs=kwargs, loop=loop).armor_decorator(fn)

    if fn is None:
        return wrapper

    if asyncio.iscoroutinefunction(unpartial(fn)):
        return wrapper(fn)

    assert not cls, 'shield like wrapper do not support cls'
    assert not kwargs, 'shield like wrapper do not support kwargs'

    return Armor().armor(fn, loop=loop)


armor.close = ArmorMeta.close
armor.reload = ArmorMeta.reload
armor.wait_closed = ArmorMeta.wait_closed
