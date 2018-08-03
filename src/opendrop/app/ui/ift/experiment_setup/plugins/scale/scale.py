import asyncio
import math
from typing import Tuple, NewType, Optional, Callable

import numpy as np
from gi.repository import Gtk

from opendrop.app.ui.core.experiment_setup.dash import ExperimentSetupDashView
from opendrop.mvp.Model import Model
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.event_container import KeyCode
from opendrop.observer.bases import Observation
from opendrop.utility import data_binding
from opendrop.utility.events import handler
from opendrop.widgets.float_entry import FloatEntry
from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup
from opendrop.app.models.experiments.ift.experiment_setup import IFTExperimentSetup
from opendrop.app.ui.core.experiment_setup import plugins
from opendrop.app.ui.core.experiment_setup.plugin import ExperimentSetupPlugin
from opendrop.app.ui.core.experiment_setup.plugins.region_selection import RegionSelectionPluginHelper

from .needle_diameter import needle_diameter_from_image


PointFloat2D = NewType('PointFloat2D', Tuple[float, float])
RectFloat = NewType('RectFloat', Tuple[PointFloat2D, PointFloat2D])

Millimetre = NewType('Millimetre', float)
Nanometre = NewType('Nanometre', float)

SELECT_NEEDLE_REGION_HOTKEY = KeyCode.N  # type: KeyCode


def str_from_float(v: Optional[float]) -> str:
    if v is None or math.isnan(v):
        return ''

    return str(v)


def float_from_str(v: str) -> float:
    try:
        return float(v)
    except ValueError:
        return math.nan


class PluginModel(Model):
    def __init__(self, experiment_setup_model: IFTExperimentSetup):
        super().__init__()

        self.experiment_setup_model = experiment_setup_model  # type: IFTExperimentSetup

        self._needle_region = ((0, 0), (0, 0))  # type: RectFloat
        self._needle_width_px = math.nan  # type: float
        self._scale = math.nan  # type: Nanometre

        self.experiment_setup_model.events.on_needle_width_changed.connect(self.recalculate_scale)

        self.routes = [
            *data_binding.Route.both(type(self.experiment_setup_model).scale, type(self).scale)
        ]

        data_binding.bind(self.experiment_setup_model, self, routes=self.routes)
        data_binding.poke(self.experiment_setup_model)

    @property
    def needle_width(self) -> float:
        if self.experiment_setup_model.needle_width is None:
            return math.nan

        return self.experiment_setup_model.needle_width

    @data_binding.property
    def needle_region(self) -> RectFloat:
        return self._needle_region

    @needle_region.setter
    def needle_region(self, value: RectFloat) -> None:
        self._needle_region = value

        self.update_needle_width_px(lambda *args: self.recalculate_scale())

    @data_binding.property
    def scale(self) -> float:
        return self._scale

    @scale.setter
    def scale(self, value) -> None:
        if value is None:
            value = math.nan

        if self.scale == value or math.isnan(self.scale) and math.isnan(value):
            return

        self._scale = value

        self.needle_region = ((0, 0), (0, 0))

        self.validate()

    def recalculate_scale(self):
        new_scale = self.needle_width / self._needle_width_px

        if math.isnan(new_scale):
            return

        self._scale = new_scale

        data_binding.poke(self, type(self).scale)

    def update_needle_width_px(self, cb: Optional[Callable] = None) -> None:
        assert self.experiment_setup_model.observer is not None

        observation = self.experiment_setup_model.observer.timelapse([0])[0]  # type: Observation

        async def f():
            image = await observation  # type: np.ndarray

            # [1::-1] means get first two elements and reverse, since the first two numbers are the image dimensions in
            # height, width format and the third number is the color depth of the image.
            needle_region_px = (np.array(self._needle_region) * image.shape[1::-1]).astype(int)

            # Normalise the region so first point is top-left, second point is bottom-right
            needle_region_px.sort(axis=0)

            image = image[needle_region_px[0][1]:needle_region_px[1][1], needle_region_px[0][0]:needle_region_px[1][0]]

            try:
                self._needle_width_px = needle_diameter_from_image(image)
            except ValueError:
                self._needle_width_px = math.nan

        future = asyncio.get_event_loop().create_task(f())  # type: asyncio.Future

        if cb is not None:
            future.add_done_callback(cb)

    def validate(self):
        pass


class Plugin(ExperimentSetupPlugin):
    @classmethod
    def should_load(cls, model: ExperimentSetup) -> bool:
        return isinstance(model, IFTExperimentSetup)

    def setup(self) -> None:
        self.plugin_model = PluginModel(self.experiment_setup_model)
        self.plugin_model.events.connect_handlers(self, 'plugin_model')

        self.dash_view = self.experiment_setup_view.spawn(DashView, model=self.plugin_model, child=True)
        self.dash_view.events.connect_handlers(self, 'dash_view')
        self.experiment_setup_view.add_dash(self.dash_view)

        self.needle_region_selection_helper = self.load_helper(
            RegionSelectionPluginHelper,
            selection_color=(128, 255, 0)
        )  # type: RegionSelectionPluginHelper
        self.needle_region_selection_helper.events.connect_handlers(self, 'needle_region_selection_helper')

        self.routes_rshelper_to_dview = [
            data_binding.Route.a_to_b(type(self.needle_region_selection_helper).selecting,
                                      type(self.dash_view).select_needle_region_btn_state)
        ]

        self.routes_model_to_rshelper = [
            *data_binding.Route.both(type(self.plugin_model).needle_region,
                                     type(self.needle_region_selection_helper).selection)
        ]

        self.routes_model_to_dview = [
            *data_binding.Route.both(type(self.plugin_model).scale, type(self.dash_view).scale)
        ]

        self.binds = [
            data_binding.bind(self.needle_region_selection_helper, self.dash_view, self.routes_rshelper_to_dview),
            data_binding.bind(self.plugin_model, self.needle_region_selection_helper, self.routes_model_to_rshelper),
            data_binding.bind(self.plugin_model, self.dash_view, self.routes_model_to_dview)
        ]

        data_binding.poke(self.plugin_model)

    @handler('dash_view', 'select_needle_region_btn.on_clicked')
    def handle_dash_view_select_region_btn_toggled(self) -> None:
        self.needle_region_selection_helper.begin_selecting()

    @handler('experiment_setup_view', 'on_key_press')
    def handle_experiment_setup_key_press(self, code: KeyCode) -> None:
        if code.lower() == SELECT_NEEDLE_REGION_HOTKEY.lower():
            if not self.needle_region_selection_helper.selecting:
                self.needle_region_selection_helper.begin_selecting()
            else:
                self.needle_region_selection_helper.end_selecting()


class DashView(ExperimentSetupDashView):
    ID = 'scale'
    NAME = 'Scale'

    def setup(self):
        body = Gtk.Grid(column_spacing=5, row_spacing=5)

        # Manual
        scale_lbl = Gtk.Label('Scale (mm/px):')
        body.attach(scale_lbl, 0, 0, 1, 1)

        scale_input_container = Gtk.Grid()
        scale_input_container.get_style_context().add_class('linked')
        body.attach(scale_input_container, 1, 0, 1, 1)

        self.scale_input = FloatEntry(min=0, hexpand=True)
        print('connect to changed')
        self.scale_input.connect('changed', self.handle_scale_input_changed)
        self.scale_input.connect('activate', lambda w: self.focus_none())
        # self.scale_input.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'dialog-error')
        scale_input_container.attach(self.scale_input, 0, 0, 1, 1)

        self.select_needle_region_btn = Gtk.Button.new_from_icon_name('list-add', Gtk.IconSize.BUTTON)
        self.select_needle_region_btn.props.tooltip_text = 'Calculate using needle in image (Hotkey: {})' \
                                                           .format(SELECT_NEEDLE_REGION_HOTKEY.name)
        self.select_needle_region_btn.connect('clicked',
                                              lambda w: self.events['select_needle_region_btn.on_clicked'].fire())

        scale_input_container.attach(self.select_needle_region_btn, 1, 0, 1, 1)

        self.container.add(body)

        body.show_all()

    @data_binding.property
    def select_needle_region_btn_state(self) -> bool:
        return not self.select_needle_region_btn.props.sensitive

    @select_needle_region_btn_state.setter
    def select_needle_region_btn_state(self, value: bool) -> None:
        self.select_needle_region_btn.props.sensitive = not value

    @data_binding.property
    def scale(self) -> Optional[float]:
        return self.scale_input.props.value

    @scale.setter
    def scale(self, value: Optional[float]) -> None:
        self.scale_input.handler_block_by_func(self.handle_scale_input_changed)
        self.scale_input.props.value = value
        self.scale_input.handler_unblock_by_func(self.handle_scale_input_changed)

    def handle_scale_input_changed(self, widget: Gtk.Widget):
        data_binding.poke(self, type(self).scale)

    def focus_none(self) -> None:
        toplevel = self.container.get_toplevel()  # type: Gtk.Widget

        if isinstance(toplevel, Gtk.Window):
            toplevel.set_focus(None)


class DashPresenter(Presenter[PluginModel, DashView]):
    pass


plugins.register_plugin(Plugin)
