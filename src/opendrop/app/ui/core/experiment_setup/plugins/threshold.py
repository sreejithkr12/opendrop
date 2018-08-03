import asyncio
from typing import Tuple, NewType

import numpy as np
from gi.repository import Gtk

from opendrop.app.ui.core.experiment_setup.dash import ExperimentSetupDashView
from opendrop.image_filter.canny_edge_detection import CannyEdgeDetection
from opendrop.mvp.Model import Model
from opendrop.mvp.Presenter import Presenter
from opendrop.observer.bases import Observation
from opendrop.utility import data_binding, comvis
from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup

from .. import plugins
from ..plugin import ExperimentSetupPlugin

PointFloat2D = NewType('PointFloat2D', Tuple[float, float])
RectFloat = NewType('RectFloat', Tuple[PointFloat2D, PointFloat2D])


class PluginModel(Model):
    def __init__(self, experiment_setup_model: ExperimentSetup) -> None:
        super().__init__()

        self.experiment_setup_model = experiment_setup_model  # type: ExperimentSetup

        self.canny_edge_filter = CannyEdgeDetection()
        self.canny_edge_filter.z_index = 0

        self._min_threshold = 30  # type: float
        self._max_threshold = 60  # type: float

        self.routes = [
            *data_binding.Route.both(type(self.canny_edge_filter).min_threshold, type(self).min_threshold),
            *data_binding.Route.both(type(self.canny_edge_filter).max_threshold, type(self).max_threshold),
        ]

        data_binding.bind(self.canny_edge_filter, self, routes=self.routes)

        data_binding.poke(self)

        self.auto_threshold()

        self.experiment_setup_model.postproc.add(self.canny_edge_filter)

    def auto_threshold(self) -> None:
        assert self.experiment_setup_model.observer is not None

        observation = self.experiment_setup_model.observer.timelapse([0])[0]  # type: Observation

        async def f():
            image = await observation  # type: np.ndarray

            self.max_threshold = comvis.otsu_threshold_val(image)
            self.min_threshold = self.max_threshold / 2

        asyncio.get_event_loop().create_task(f())  # type: asyncio.Future

    @data_binding.property
    def min_threshold(self) -> float:
        return self._min_threshold

    @min_threshold.setter
    def min_threshold(self, value: float) -> None:
        self._min_threshold = value

    @data_binding.property
    def max_threshold(self) -> float:
        return self._max_threshold

    @max_threshold.setter
    def max_threshold(self, value: float) -> None:
        self._max_threshold = value


class CannyEdgeOverlay(CannyEdgeDetection):
    # -1 so that it is applied before UI overlay elements
    z_index = -1

    def __init__(self, overlay_colour: Tuple[int, int, int], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._overlay_colour = overlay_colour

    def apply(self, image: np.ndarray) -> np.ndarray:
        orig_image = image.copy()  # type: np.ndarray

        mask = super().apply(image) / 255  # type: np.ndarray
        mask *= self._overlay_colour

        image = (orig_image + mask).clip(0, 255).astype(np.uint8)

        return image


class Plugin(ExperimentSetupPlugin):
    @classmethod
    def should_load(cls, model: ExperimentSetup) -> bool:
        return True

    def setup(self) -> None:
        self.plugin_model = PluginModel(self.experiment_setup_model)

        self.dash_view = self.experiment_setup_view.spawn(DashView, model=self.experiment_setup_model,
                                                          child=True)  # type: DashView
        self.dash_view.events.connect_handlers(self, 'dash_view')
        self.experiment_setup_view.add_dash(self.dash_view)

        self.canny_edge_overlay = CannyEdgeOverlay(overlay_colour=(0, 128, 255))
        self.canny_edge_overlay.events.on_dirtied.connect(self.experiment_setup_view.redraw_viewer)
        self.experiment_setup_view.viewer_add_filter(self.canny_edge_overlay)

        self.routes_plugin_model_to_dview = [
            *data_binding.Route.both(type(self.plugin_model).min_threshold, type(self.dash_view).min_threshold),
            *data_binding.Route.both(type(self.plugin_model).max_threshold, type(self.dash_view).max_threshold)
        ]

        self.routes_plugin_model_to_ceoverlay = [
            data_binding.Route.a_to_b(type(self.plugin_model).min_threshold,
                                      type(self.canny_edge_overlay).min_threshold),
            data_binding.Route.a_to_b(type(self.plugin_model).max_threshold,
                                      type(self.canny_edge_overlay).max_threshold)
        ]

        data_binding.bind(self.plugin_model, self.dash_view, routes=self.routes_plugin_model_to_dview)
        data_binding.bind(self.plugin_model, self.canny_edge_overlay, routes=self.routes_plugin_model_to_ceoverlay)

        data_binding.poke(self.plugin_model)


class DashView(ExperimentSetupDashView):
    ID = 'threshold'
    NAME = 'Canny edge detection'

    def setup(self):
        body = Gtk.Grid(column_spacing=5, row_spacing=5)

        max_threshold_lbl = Gtk.Label('Max threshold:')
        body.attach(max_threshold_lbl, 0, 0, 1, 1)

        def handle_max_threshold_input_value_changed(w: Gtk.Adjustment):
            rel_min_val = self.min_threshold_input.props.value / self.min_threshold_input.props.upper

            self.min_threshold_input.props.upper = w.props.value
            self.min_threshold_input.props.value = rel_min_val * self.min_threshold_input.props.upper

            data_binding.poke(self, type(self).max_threshold)

        self.max_threshold_input = Gtk.Adjustment(value=1, lower=1, upper=255)
        self.max_threshold_input.connect('value-changed', handle_max_threshold_input_value_changed)

        max_threshold_scale = Gtk.Scale.new(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.max_threshold_input)
        max_threshold_scale.props.hexpand = True
        body.attach(max_threshold_scale, 1, 0, 1, 1)

        min_threshold_lbl = Gtk.Label('Min threshold:')
        body.attach(min_threshold_lbl, 0, 1, 1, 1)

        def handle_min_threshold_input_value_changed(w: Gtk.Adjustment):
            data_binding.poke(self, type(self).min_threshold)

        self.min_threshold_input = Gtk.Adjustment(value=0, lower=0, upper=1)
        self.min_threshold_input.connect('value-changed', handle_min_threshold_input_value_changed)

        min_threshold_scale = Gtk.Scale.new(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.min_threshold_input)
        min_threshold_scale.props.hexpand = True
        body.attach(min_threshold_scale, 1, 1, 1, 1)

        body.show_all()

        self.container.add(body)

    @data_binding.property
    def max_threshold(self) -> float:
        return self.max_threshold_input.props.value

    @max_threshold.setter
    def max_threshold(self, value: float) -> None:
        self.max_threshold_input.props.value = value

    @data_binding.property
    def min_threshold(self) -> float:
        return self.min_threshold_input.props.value

    @min_threshold.setter
    def min_threshold(self, value: float) -> None:
        self.min_threshold_input.props.value = value


class DashPresenter(Presenter[None, DashView]):
    pass


plugins.register_plugin(Plugin)
