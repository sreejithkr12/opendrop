import importlib
import inspect
import pkgutil
from enum import Enum
from types import ModuleType
from typing import Union, Optional, Any, Type, List, Iterable, TypeVar, Generic, overload

import numpy as np
from numpy.lib.stride_tricks import as_strided

T = TypeVar('T')


def recursive_load(pkg: Union[ModuleType, str]) -> List[ModuleType]:
    pkg = importlib.import_module(pkg) if isinstance(pkg, str) else pkg  # type: ModuleType

    loaded_modules = [pkg]  # type: List[ModuleType]

    if hasattr(pkg, '__path__'):
        for loader, name, is_pkg in pkgutil.iter_modules(pkg.__path__):
            full_name = pkg.__name__ + '.' + name
            child = importlib.import_module(full_name)
            loaded_modules += recursive_load(child)

    return loaded_modules


def get_classes_in_modules(m: Union[Iterable[ModuleType], ModuleType], cls: T) -> List[T]:
    clses = []  # type: List[Type]

    if isinstance(m, Iterable):
        for v in m:
            clses += get_classes_in_modules(v, cls)

        return clses

    for name in dir(m):
        attr = getattr(m, name)

        if inspect.isclass(attr) and issubclass(attr, cls) and attr.__module__ == m.__name__:
            clses.append(attr)

    return clses


# No longer used by anything, probably delete in the future
class EnumBuilder:
    def __init__(self, value: str, type: Optional[type] = None) -> None:
        self._value = value
        self._type = type
        self._names = {}

    def add(self, name: str, val: Any) -> None:
        self._names[name] = val

    def remove(self, name: str) -> None:
        del self._names[name]

    def build(self):
        return Enum(self._value, names=self._names, type=self._type)


def slice_view(a: np.ndarray, start: Iterable[int], stop: Iterable[int]):
    start = np.array(start)
    stop = np.array(stop)

    assert len(start) == len(stop) == len(a.shape)

    offset = sum(start * a.strides) // a.itemsize
    a_offset = np.reshape(a, -1)[offset:]

    return as_strided(a_offset, shape=(stop-start), strides=a.strides)


NT = TypeVar('NT', int, float, complex)

class Rect(Generic[NT]):
    @overload
    def __init__(self, *, x0: NT, y0: NT, x1: NT, y1: NT): ...

    @overload
    def __init__(self, *, x: NT, y: NT, w: NT, h: NT): ...

    def __init__(self, **kwargs: NT):
        if 'x' in kwargs:
            x0, y0 = kwargs.pop('x'), kwargs.pop('y')
            x1, y1 = x0 + kwargs.pop('w'), y0 + kwargs.pop('h')
            if kwargs:
                raise ValueError("Expected only ('x', 'y', 'w', 'h'), got {} extra".format(kwargs.keys()))
        elif 'x0' in kwargs:
            x0, y0 = kwargs.pop('x0'), kwargs.pop('y0')
            x1, y1 = kwargs.pop('x1'), kwargs.pop('y1')
            if kwargs:
                raise ValueError("Expected only ('x0', 'y0', 'x1', 'y1'), got {} extra".format(tuple(kwargs.keys())))
        else:
            raise ValueError('Unrecognised arguments {}'.format(kwargs.keys()))

        self._x0 = x0
        self._y0 = y0
        self._x1 = x1
        self._y1 = y1

        if x0 > x1:
            self._x0, self._x1 = x1, x0

        if y0 > y1:
            self._y0, self._y1 = y1, y0

    @property
    def x0(self) -> NT:
        return self._x0

    @property
    def y0(self) -> NT:
        return self._y0

    x, y = x0, y0

    @property
    def x1(self) -> NT:
        return self._x1

    @property
    def y1(self) -> NT:
        return self._y1

    @property
    def w(self) -> NT:
        return self.x1 - self.x0

    @property
    def h(self) -> NT:
        return self.y1 - self.y0

    def __repr__(self) -> str:
        return '{class_name}(x0={self.x0}, y0={self.y0}, x1={self.x1}, y1={self.y1})'\
               .format(class_name=type(self).__name__, self=self)
