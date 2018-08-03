import math
from typing import Optional

from gi.repository import Gtk

from opendrop.app.ui.core.experiment_setup.dash import ExperimentSetupDashView
from opendrop.mvp.Presenter import Presenter
from opendrop.utility import data_binding
from opendrop.widgets.float_entry import FloatEntry
from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup
from opendrop.app.models.experiments.ift.experiment_setup import IFTExperimentSetup
from opendrop.app.ui.core.experiment_setup import plugins
from opendrop.app.ui.core.experiment_setup.plugin import ExperimentSetupPlugin


def str_from_float(v: Optional[float]) -> str:
    if v is None or math.isnan(v):
        return ''

    return str(v)


class Plugin(ExperimentSetupPlugin):
    @classmethod
    def should_load(cls, model: ExperimentSetup) -> bool:
        return isinstance(model, IFTExperimentSetup)

    def setup(self) -> None:
        self.dash_view = self.experiment_setup_view.spawn(DashView, child=True)
        self.experiment_setup_view.add_dash(self.dash_view)

        self.routes = [
            *data_binding.Route.both(type(self.experiment_setup_model).inner_density,
                                     type(self.dash_view).inner_density),
            *data_binding.Route.both(type(self.experiment_setup_model).outer_density,
                                     type(self.dash_view).outer_density),
            *data_binding.Route.both(type(self.experiment_setup_model).needle_width,
                                     type(self.dash_view).needle_width)
        ]

        data_binding.bind(self.experiment_setup_model, self.dash_view, routes=self.routes)
        data_binding.poke(self.experiment_setup_model)


class DashView(ExperimentSetupDashView):
    ID = 'physical_quantities'
    NAME = 'Physical quantities'

    def setup(self):
        self.body = Gtk.Grid(column_spacing=5, row_spacing=5)

        inner_density_lbl = Gtk.Label('Inner density (kg/m³):', halign=Gtk.Align.START)
        self.body.attach(inner_density_lbl, 0, 0, 1, 1)

        self.inner_density_input = FloatEntry(min=0, hexpand=True)
        self.inner_density_input.connect('changed', lambda w: data_binding.poke(self, type(self).inner_density))
        self.inner_density_input.connect('activate', lambda w: self.outer_density_input.grab_focus())
        self.body.attach(self.inner_density_input, 1, 0, 1, 1)

        outer_density_lbl = Gtk.Label('Outer density (kg/m³):', halign=Gtk.Align.START)
        self.body.attach(outer_density_lbl, 0, 1, 1, 1)

        self.outer_density_input = FloatEntry(min=0, hexpand=True)
        self.outer_density_input.connect('changed', lambda w: data_binding.poke(self, type(self).outer_density))
        self.outer_density_input.connect('activate', lambda w: self.needle_width_input.grab_focus())
        self.body.attach(self.outer_density_input, 1, 1, 1, 1)

        needle_width_lbl = Gtk.Label('Needle diameter (mm):', halign=Gtk.Align.START)
        self.body.attach(needle_width_lbl, 0, 2, 1, 1)

        self.needle_width_input = FloatEntry(min=0, hexpand=True)
        self.needle_width_input.connect('changed', lambda w: data_binding.poke(self, type(self).needle_width))
        self.needle_width_input.connect('activate', lambda w: self.focus_none())
        self.body.attach(self.needle_width_input, 1, 2, 1, 1)

        self.body.show_all()

        self.container.add(self.body)

    @data_binding.property
    def inner_density(self) -> Optional[float]:
        return self.inner_density_input.props.value

    @inner_density.setter
    def inner_density(self, value: Optional[float]) -> None:
        self.inner_density_input.props.value = value

    @data_binding.property
    def outer_density(self) -> Optional[float]:
        return self.outer_density_input.props.value

    @outer_density.setter
    def outer_density(self, value: Optional[float]) -> None:
        self.outer_density_input.props.value = value

    @data_binding.property
    def needle_width(self) -> Optional[float]:
        return self.needle_width_input.props.value

    @needle_width.setter
    def needle_width(self, value: Optional[float]) -> None:
        self.needle_width_input.props.value = value

    def focus_none(self) -> None:
        toplevel = self.body.get_toplevel()  # type: Gtk.Widget

        if isinstance(toplevel, Gtk.Window):
            toplevel.set_focus(None)


class DashPresenter(Presenter[None, DashView]):
    pass


plugins.register_plugin(Plugin)
