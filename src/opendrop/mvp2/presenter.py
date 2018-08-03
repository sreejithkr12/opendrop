from typing import Generic, TypeVar, Optional

from opendrop.mvp2.datatypes import ViewPresenterState

# setup() and teardown() should not be called internally, they are part of the public interface, for public use only.

VT = TypeVar('VT')


class Presenter(Generic[VT]):
    def __init__(self, **passthrough_opts):
        self._state = ViewPresenterState.INITIALISING
        self._view = None  # type: Optional[VT]

        self._m_init(**passthrough_opts)
        self._state = ViewPresenterState.INITIALISED

    def set_up(self) -> None:
        if self._state is not ViewPresenterState.INITIALISED:
            raise ValueError("Presenter is in state `{!s}`, but set_up() can only be called if it is in state `{!s}`"
                             .format(self._state, ViewPresenterState.INITIALISED))
        if self.view is None:
            raise ValueError("Can't set up presenter when assigned view is None".format(self=self))
        elif self.view.state is not ViewPresenterState.UP:
            raise ValueError("Can't set up presenter when assigned view is not set up")

        self._state = ViewPresenterState.SETTING_UP
        self._set_up()
        self._state = ViewPresenterState.UP

    def tear_down(self) -> None:
        if self._state is not ViewPresenterState.UP:
            raise ValueError("Presenter is in state `{!s}`, but tear_down() can only be called if it is in state `{!s}`"
                             .format(self._state, ViewPresenterState.UP))

        self._state = ViewPresenterState.TEARING_DOWN
        self._tear_down()
        self._state = ViewPresenterState.DOWN

    # To be overrided by subclasses.
    def _m_init(self, **kwargs): pass

    def _set_up(self): pass

    def _tear_down(self): pass

    # Read-only passthrough
    @property
    def state(self) -> ViewPresenterState:
        return self._state

    @property
    def view(self):
        return self._view

    @view.setter
    def view(self, value):
        if self._state is not ViewPresenterState.INITIALISED:
            raise ValueError("Can't modify view after presenter is set up")

        self._view = value
