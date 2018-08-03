from opendrop.mvp2.datatypes import ViewPresenterState


class View:
    def __init__(self, **passthrough_opts):
        self._state = ViewPresenterState.INITIALISING
        self._m_init(**passthrough_opts)
        self._state = ViewPresenterState.INITIALISED

    def set_up(self):
        if self._state is not ViewPresenterState.INITIALISED:
            raise ValueError("View is in state `{!s}`, but set_up() can only be called if it is in state `{!s}`"
                             .format(self._state, ViewPresenterState.INITIALISED))

        self._state = ViewPresenterState.SETTING_UP
        self._set_up()
        self._state = ViewPresenterState.UP

    def tear_down(self):
        if self._state is not ViewPresenterState.UP:
            raise ValueError("View is in state `{!s}`, but tear_down() can only be called if it is in state `{!s}`"
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
    def state(self):
        return self._state