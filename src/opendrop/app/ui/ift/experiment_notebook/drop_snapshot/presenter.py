import math

from opendrop.app.models.experiments.ift.drop_snapshot import DropSnapshot
from opendrop.mvp.Presenter import Presenter
from opendrop.utility.events import handler, HasEvents, EventSource

from .view import DropSnapshotView


class Log(HasEvents):
    def __init__(self):
        self.events = EventSource()

        self.contents = ''

    def write(self, msg: str) -> None:
        self.contents += msg

        self.events.on_changed.fire()


class DropSnapshotPresenter(Presenter[DropSnapshot, DropSnapshotView]):
    def setup(self):
        self.log_file = Log()
        self.model.log_file = self.log_file
        self.log_file.events.connect_handlers(self, 'log_file')

    @handler('log_file', 'on_changed')
    def handle_log_file_changed(self) -> None:
        self.view.set_log_text(self.log_file.contents)

    @handler('model', 'on_image_loaded')
    def handle_drop_snapshot_image_loaded(self) -> None:
        self.view.set_drop_image(self.model.drop_image)
        self.view.set_drop_image_scale(self.model.scale)

    @handler('model', 'on_drop_contour_changed')
    def handle_drop_snapshot_drop_contour_changed(self) -> None:
        self.view.set_drop_contour(self.model.drop_contour)

    @handler('model', 'on_residuals_changed')
    def handle_drop_snapshot_residuals_changed(self) -> None:
        self.view.set_fit_residuals(self.model.residuals)

    @handler('model', 'on_params_changed')
    def handle_params_changed(self) -> None:
        params = {
          'ift': self.model.derived.ift,
          'volume': self.model.derived.volume,
          'surface_area': self.model.derived.surface_area,
          'worthington': self.model.derived.worthington,
          'apex': (round(self.model.apex_x), round(self.model.apex_y)),
          'apex_radius': self.model.fit.apex_radius,
          'image_angle': math.degrees(self.model.fit.apex_rot),
          'bond': self.model.fit.bond,
        }

        self.view.update_params(params)

        self.view.set_drop_contour_fitted(self.model.drop_contour_fitted)
