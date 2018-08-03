from typing import NewType, Tuple, Optional

import numpy as np

from opendrop.image_filter.rectangle_drawer import RectangleDrawer
from opendrop.mvp.event_container import MouseMoveEvent, MouseButtonEvent, MouseButtonType, KeyCode
from opendrop.utility import data_binding
from opendrop.utility.events import EventSource, handler
from opendrop.utility.events.events import HasEvents

from ..plugin import ExperimentSetupPlugin
from ..presenter import LockChild

PointFloat2D = NewType('PointFloat2D', Tuple[float, float])
RectFloat = NewType('RectFloat', Tuple[PointFloat2D, PointFloat2D])


class RegionSelectionPluginHelper(ExperimentSetupPlugin, HasEvents):
    @classmethod
    def should_load(cls, *args, **kwargs):
        # Since this is a plugin helper, it should never be loaded automatically
        return False

    def __init__(self, *args, **kwargs):
        self.events = EventSource()

        super().__init__(*args, **kwargs)

    def setup(self, selection_color: Tuple[int, int, int] = (0, 0, 0)) -> None:
        self._selecting = False
        self._selection = ((0, 0), (0, 0))

        self.region_selection_manager = RegionSelectionManager()

        self.activity_lock = self.experiment_setup_presenter.activity_locks.get()  # type: Optional[LockChild]

        self.rect_drawer = RectangleDrawer(selection_color)  # type: RectangleDrawer

        self.experiment_setup_view.viewer_add_filter(self.rect_drawer)

        self.routes_rsmgr_to_rect_drawer = [
            data_binding.Route.a_to_b(type(self.region_selection_manager).selection_current,
                                      type(self.rect_drawer).rect)
        ]

        self.routes_rsmgr_to_self = [
            *data_binding.Route.both(type(self.region_selection_manager).selection, type(self).selection)
        ]

        data_binding.bind(self.region_selection_manager, self.rect_drawer, self.routes_rsmgr_to_rect_drawer)
        data_binding.bind(self.region_selection_manager, self, self.routes_rsmgr_to_self)

        self.region_selection_manager.events.connect_handlers(self, 'region_selection_manager')
        self.rect_drawer.events.connect_handlers(self, 'rect_drawer')
        self.activity_lock.events.connect_handlers(self, 'activity_lock')

    @handler('experiment_setup_view', 'viewer.on_mouse_move')
    def handle_viewer_mouse_move(self, event: MouseMoveEvent) -> None:
        self.region_selection_manager.cursor = event.pos

    @handler('experiment_setup_view', 'viewer.on_button_press')
    def handle_viewer_button_press(self, event: MouseButtonEvent) -> None:
        if event.button == MouseButtonType.L_BUTTON:
            self.region_selection_manager.cursor = event.pos
            self.region_selection_manager.cursor_state = True

    @handler('experiment_setup_view', 'viewer.on_button_release')
    def handle_viewer_button_release(self, event: MouseButtonEvent) -> None:
        if event.button == MouseButtonType.L_BUTTON:
            self.region_selection_manager.cursor = event.pos
            self.region_selection_manager.cursor_state = False

    @handler('experiment_setup_view', 'viewer.on_focus_out')
    def handle_viewer_focus_out(self) -> None:
        self.end_selecting()

    @handler('experiment_setup_view', 'on_mouse_button_press')
    def handle_mouse_button_press(self, event: MouseButtonEvent) -> None:
        if event.button in (MouseButtonType.R_BUTTON,):
            self.end_selecting()

    @handler('experiment_setup_view', 'on_key_press')
    def handle_mouse_button_press(self, key_code: KeyCode) -> None:
        if key_code == KeyCode.ESC:
            self.end_selecting()

    @handler('rect_drawer', 'on_dirtied')
    def handle_rect_drawer_dirtied(self):
        self.experiment_setup_view.redraw_viewer()

    @handler('activity_lock', 'on_released')
    def handle_activity_lock_released(self):
        if self.selecting:
            self._raw_end_selecting()

    @handler('region_selection_manager', 'on_selection_changed')
    def handle_region_selection_manager_selection_changed(self):
        self.end_selecting()

    def _raw_begin_selecting(self):
        assert self.activity_lock.active

        self.region_selection_manager.active = True
        self.experiment_setup_view.cursor_set_crosshair(True)
        self.experiment_setup_view.viewer_grab_focus()

        self.selecting = True

    def _raw_end_selecting(self):
        self.region_selection_manager.active = False
        self.experiment_setup_view.cursor_set_crosshair(False)

        self.selecting = False

    def begin_selecting(self):
        if self.selecting:
            return

        self.activity_lock.acquire()
        self._raw_begin_selecting()

    def end_selecting(self):
        if not self.selecting:
            return

        self._raw_end_selecting()
        self.activity_lock.release()

    @data_binding.property
    def selecting(self) -> bool:
        return self._selecting

    @selecting.setter
    def selecting(self, value: bool) -> None:
        self._selecting = value

        self.events.on_selecting_changed.fire()

    @data_binding.property
    def selection(self) -> RectFloat:
        return self._selection

    @selection.setter
    def selection(self, value: RectFloat) -> None:
        self._selection = value

    @property
    def selection_color(self) -> Tuple[int, int, int]:
        return self.rect_drawer.color

    @selection_color.setter
    def selection_color(self, value: Tuple[int, int, int]) -> None:
        self.rect_drawer.color = value


class RegionSelectionManager(HasEvents):
    def __init__(self) -> None:
        self.events = EventSource()

        self._active = False  # type: bool

        self._selection_current = ((0, 0), (0, 0))  # type: RectFloat

        self._selection = ((0, 0), (0, 0))  # type: RectFloat

        self._cursor = (0, 0)  # type: PointFloat2D
        self._cursor_state = False  # type: bool

    def _commit_selection_current(self) -> None:
        self.selection = self.selection_current

    def _discard_selection_current(self) -> None:
        self.selection_current = self.selection

    def begin(self):
        if self.active:
            return

        self.active = True

    def end(self):
        if not self.active:
            return

        self.active = False

        self._discard_selection_current()

    @data_binding.property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        self._active = value

        if value is False:
            self._discard_selection_current()

    @data_binding.property
    def selection_current(self) -> RectFloat:
        return self._selection_current

    @selection_current.setter
    def selection_current(self, value: RectFloat) -> None:
        self._selection_current = value

    @data_binding.property
    def selection(self) -> RectFloat:
        return self._selection

    @selection.setter
    def selection(self, value: RectFloat) -> None:
        value = np.clip(value, 0, 1)

        self._selection = value

        self.selection_current = value

        self.events.on_selection_changed.fire()

    @property
    def cursor(self) -> PointFloat2D:
        return self._cursor

    @cursor.setter
    def cursor(self, value: PointFloat2D) -> None:
        self._cursor = value

        if self.active and self.cursor_state:
            self.selection_current = self.selection_current[0], self.cursor

    @property
    def cursor_state(self) -> bool:
        return self._cursor_state

    @cursor_state.setter
    def cursor_state(self, value: bool) -> None:
        self._cursor_state = value

        if self.active:
            if self.cursor_state:
                self.selection_current = self.cursor, self.cursor
            else:
                self.selection_current = self.selection_current[0], self.cursor
                self._commit_selection_current()
