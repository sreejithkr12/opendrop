from typing import Optional, List

from gi.repository import Gtk

from opendrop.app.ui.core.experiment_setup.dash import ExperimentSetupDashView
from opendrop.mvp.Model import Model
from opendrop.mvp.Presenter import Presenter
from opendrop.utility import data_binding
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry

from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup


class PluginModel(Model):
    def __init__(self, experiment_setup_model: ExperimentSetup):
        super().__init__()

        self.experiment_setup_model = experiment_setup_model  # type: ExperimentSetup

        self._num_frames = 5  # type: Optional[int]
        self._frame_interval = 10  # type: Optional[float]

        self.routes = [
            *data_binding.Route.both(type(self.experiment_setup_model).frame_timestamps, type(self).frame_timestamps)
        ]

        data_binding.bind(self.experiment_setup_model, self, self.routes)
        data_binding.poke(self.experiment_setup_model)

    @data_binding.property
    def num_frames(self) -> int:
        return self._num_frames

    @num_frames.setter
    def num_frames(self, value: int) -> None:
        self._num_frames = value
        data_binding.poke(self, type(self).frame_timestamps)

    @data_binding.property
    def frame_interval(self) -> Optional[float]:
        return self._frame_interval

    @frame_interval.setter
    def frame_interval(self, value: Optional[float]) -> None:
        self._frame_interval = value
        data_binding.poke(self, type(self).frame_timestamps)

    @data_binding.property
    def frame_timestamps(self) -> List[float]:
        if self.num_frames is None:
            return []

        if self.frame_interval is None or self.frame_interval == 0:
            if self.num_frames == 1:
                return [0]
            else:
                return []

        return [i * self.frame_interval for i in range(self.num_frames)]

    @frame_timestamps.setter
    def frame_timestamps(self, value: List[float]) -> None:
        self.num_frames = len(value)

        if len(value) > 1:
            self.frame_interval = value[1] - value[0]
        else:
            self.frame_interval = None


class DashView(ExperimentSetupDashView):
    ID = 'observations_config'
    NAME = 'Observations'

    def setup(self):
        body = Gtk.Grid(column_spacing=5, row_spacing=5)

        num_frames_lbl = Gtk.Label('Number of frames:', halign=Gtk.Align.START)
        body.attach(num_frames_lbl, 0, 0, 1, 1)

        self.num_frames_input = IntegerEntry(min=0, max=1000, hexpand=True)
        self.num_frames_input.connect('changed', lambda w: data_binding.poke(self, type(self).num_frames))
        self.num_frames_input.connect('activate', lambda w: self.frame_interval_input.grab_focus())
        body.attach(self.num_frames_input, 1, 0, 1, 1)

        frame_interval_lbl = Gtk.Label('Frame interval (s):', halign=Gtk.Align.START)
        body.attach(frame_interval_lbl, 0, 1, 1, 1)

        self.frame_interval_input = FloatEntry(min=0, hexpand=True)
        self.frame_interval_input.connect('changed', lambda w: data_binding.poke(self, type(self).frame_interval))
        self.frame_interval_input.connect('activate', lambda w: self.focus_none())
        body.attach(self.frame_interval_input, 1, 1, 1, 1)

        body.show_all()

        self.container.add(body)

    @data_binding.property
    def frame_interval(self) -> Optional[float]:
        return self.frame_interval_input.props.value

    @frame_interval.setter
    def frame_interval(self, value: Optional[float]) -> None:
        self.frame_interval_input.props.value = value

    @data_binding.property
    def num_frames(self) -> Optional[int]:
        return self.num_frames_input.props.value

    @num_frames.setter
    def num_frames(self, value: Optional[int]) -> None:
        self.num_frames_input.props.value = value

    def focus_none(self) -> None:
        toplevel = self.container.get_toplevel()  # type: Gtk.Widget

        if isinstance(toplevel, Gtk.Window):
            toplevel.set_focus(None)


class DashPresenter(Presenter[None, DashView]):
    pass
