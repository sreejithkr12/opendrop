import functools
from abc import abstractmethod
from typing import Type, overload, TypeVar, Callable, Mapping, Any

from gi.repository import Gtk

from opendrop.observer.bases import ObserverType

T = TypeVar('T')


class Configurator:
    _registration = {}

    @classmethod
    def new_for_type(cls, o_type: ObserverType) -> 'Configurator':
        if o_type not in cls._registration.keys():
            raise ValueError("Observer type '{0.name}' ({0}) not recognised".format(o_type))

        new_configurator_cls = cls._registration[o_type]
        return new_configurator_cls()

    @overload
    @classmethod
    def register_configurator(cls, o_type: ObserverType, configurator_cls: Type['Configurator']) -> None: ...

    @overload
    @classmethod
    def register_configurator(cls, o_type: ObserverType) -> Callable[[T], T]: ...

    @classmethod
    def register_configurator(cls, o_type, configurator_cls=None, _decorator: bool = False):
        if configurator_cls is None:
            return functools.partial(cls.register_configurator, o_type, _decorator=True)

        cls._registration[o_type] = configurator_cls

        if _decorator:
            return configurator_cls

    @abstractmethod
    def create_widget(self) -> Gtk.Widget:
        """Create and return a widget that modifies the imageacquisition options."""

    @property
    @abstractmethod
    def options(self) -> Mapping[str, Any]:
        """Return a key-value mapping of options to initialise the imageacquisition with."""
