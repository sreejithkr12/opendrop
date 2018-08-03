from typing import Optional, List

from opendrop.app.ui.core.experiment_setup.plugins import observations_config
from opendrop.mvp.Model import Model
from opendrop.mvp.Presenter import Presenter
from opendrop.observer.types.camera import CameraObserver
from opendrop.utility import data_binding
from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup

from .. import plugins
from ..plugin import ExperimentSetupPlugin


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


class Plugin(ExperimentSetupPlugin):
    @classmethod
    def should_load(cls, model: ExperimentSetup) -> bool:
        if isinstance(model.observer, CameraObserver):
            return True

        return False

    def setup(self) -> None:
        self.plugin_model = PluginModel(self.experiment_setup_model)

        self.dash_view = self.experiment_setup_view.spawn(DashView, child=True)
        self.experiment_setup_view.add_dash(self.dash_view)

        self.routes = [
            *data_binding.Route.both(type(self.plugin_model).frame_interval, type(self.dash_view).frame_interval),
            *data_binding.Route.both(type(self.plugin_model).num_frames, type(self.dash_view).num_frames),
        ]

        data_binding.bind(self.plugin_model, self.dash_view, routes=self.routes)
        data_binding.poke(self.plugin_model)


class DashView(observations_config.DashView):
    NAME = 'Camera'


class DashPresenter(Presenter[None, DashView]):
    pass


plugins.register_plugin(Plugin)
