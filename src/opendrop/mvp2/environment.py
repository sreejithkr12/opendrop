from abc import abstractmethod
from typing import TypeVar, Type

from typing_extensions import Protocol

from opendrop.mvp2.presenter import Presenter
from opendrop.mvp2.view import View

VT, PT = TypeVar('VT', bound=View), TypeVar('PT', bound=Presenter)
T = TypeVar('T')


class Provider(Protocol[T]):
    @abstractmethod
    def __call__(self, environment: 'Environment') -> T:
        ...


# This class would be a generic type, however, this can cause irresolvable metaclass conflicts in some subclasses.
# See https://github.com/python/typing/issues/449
# This issue is resolved in Python 3.7.
# Alternatively, redesign this class to favour composition over inheritance.
class Environment:  # Environment(Generic[MT, VT, PT]):
    def __init__(self, *passthrough_args, _view_cls: Type[VT], _presenter_cls: Type[PT], **passthrough_kwargs):
        self._view_opts = {}
        self._presenter_opts = {}

        # Perform subclass _init() here.
        self._m_init(*passthrough_args, **passthrough_kwargs)

        # Create the view and presenter.
        view = _view_cls(**self._view_opts)
        presenter = _presenter_cls(**self._presenter_opts)

        self.view = view
        self.presenter = presenter

        # Assign the presenter its view.
        self.presenter.view = view

        # Perform subclass _set_up() here.
        self._set_up()

    def _m_init(self, *args, **kwargs) -> None: pass

    def _set_up(self) -> None: pass
