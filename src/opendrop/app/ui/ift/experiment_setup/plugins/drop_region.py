from typing import Tuple, NewType, Optional

from gi.repository import Gtk

from opendrop.app.ui.core.experiment_setup.dash import ExperimentSetupDashView
from opendrop.mvp.Presenter import Presenter
from opendrop.mvp.event_container import KeyCode
from opendrop.utility import data_binding
from opendrop.utility.events import handler
from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup
from opendrop.app.models.experiments.ift.experiment_setup import IFTExperimentSetup
from opendrop.app.ui.core.experiment_setup import plugins
from opendrop.app.ui.core.experiment_setup.plugin import ExperimentSetupPlugin
from opendrop.app.ui.core.experiment_setup.plugins.region_selection import RegionSelectionPluginHelper

PointFloat2D = NewType('PointFloat2D', Tuple[float, float])
RectFloat = NewType('RectFloat', Tuple[PointFloat2D, PointFloat2D])

SELECT_REGION_HOTKEY = KeyCode.R  # type: KeyCode


class Plugin(ExperimentSetupPlugin):
    @classmethod
    def should_load(cls, model: ExperimentSetup) -> bool:
        return isinstance(model, IFTExperimentSetup)

    def setup(self) -> None:
        self.region_selection_helper = self.load_helper(
            RegionSelectionPluginHelper,
            selection_color=(255, 0, 0)
        )  # type: RegionSelectionPluginHelper

        self.dash_view = self.experiment_setup_view.spawn(DashView, model=self.experiment_setup_model, child=True)
        self.dash_view.events.connect_handlers(self, 'dash_view')
        self.experiment_setup_view.add_dash(self.dash_view)

        self.routes_rshelper_to_dview = [
            data_binding.Route.a_to_b(RegionSelectionPluginHelper.selecting, DashView.select_drop_region_btn_state)
        ]

        self.routes_model_to_rshelper = [
            *data_binding.Route.both(type(self.experiment_setup_model).drop_region,
                                     type(self.region_selection_helper).selection)
        ]

        data_binding.bind(self.region_selection_helper, self.dash_view, self.routes_rshelper_to_dview)
        data_binding.bind(self.experiment_setup_model, self.region_selection_helper, self.routes_model_to_rshelper)

        data_binding.poke(self.experiment_setup_model)

    @handler('dash_view', 'select_drop_region_btn.on_clicked')
    def handle_select_drop_region_btn_toggled(self):
        self.region_selection_helper.begin_selecting()

    @handler('experiment_setup_view', 'on_key_press')
    def handle_experiment_setup_key_press(self, code: KeyCode):
        if code.lower() == SELECT_REGION_HOTKEY.lower():
            if not self.region_selection_helper.selecting:
                self.region_selection_helper.begin_selecting()
            else:
                self.region_selection_helper.end_selecting()


class DashView(ExperimentSetupDashView):
    ID = 'drop_region'
    NAME = 'Drop region'

    def setup(self):
        self._toplevel = None

        self.body = Gtk.Grid(column_spacing=5, row_spacing=5)
        self.body.connect('parent-set', self.handle_toplevel_changed)

        drop_region_lbl = Gtk.Label('Region:')
        self.body.attach(drop_region_lbl, 0, 0, 1, 1)

        self.select_drop_region_btn = Gtk.Button(label='Select Region ({})'.format(SELECT_REGION_HOTKEY.name),
                                                 hexpand=True)

        def handle_select_drop_region_btn_clicked(w):
            data_binding.poke(self, type(self).select_drop_region_btn_state)
            self.events['select_drop_region_btn.on_clicked'].fire()

        self.select_drop_region_btn.connect('clicked', handle_select_drop_region_btn_clicked)

        self.body.attach(self.select_drop_region_btn, 1, 0, 1, 1)

        self.body.show_all()

        self.container.add(self.body)

    def handle_toplevel_changed(self, w: Gtk.Widget, old_parent: Gtk.Widget) -> None:
        while old_parent is not None:
            try:
                old_parent.disconnect_by_func(self.handle_toplevel_changed)
            except TypeError:
                pass
            old_parent = old_parent.props.parent

        new_parent = w
        while new_parent.props.parent is not None:
            new_parent.props.parent.connect('parent-set', self.handle_toplevel_changed)
            new_parent = new_parent.props.parent

        if not isinstance(new_parent, Gtk.Window):
            return

        self.toplevel = new_parent

    @property
    def toplevel(self) -> Optional[Gtk.Window]:
        return self._toplevel

    @toplevel.setter
    def toplevel(self, value: Optional[Gtk.Window]) -> None:
        if self.toplevel == value:
            return

        # if self.toplevel is not None:
        #     self.toplevel.remove_accel_group(self.accel_group)
        #
        # if value is not None:
        #     value.add_accel_group(self.accel_group)

        self._toplevel = value


    @data_binding.property
    def select_drop_region_btn_state(self) -> bool:
        return not self.select_drop_region_btn.props.sensitive

    @select_drop_region_btn_state.setter
    def select_drop_region_btn_state(self, value: bool) -> None:
        self.select_drop_region_btn.props.sensitive = not value


class DashPresenter(Presenter[None, DashView]):
    pass


plugins.register_plugin(Plugin)
