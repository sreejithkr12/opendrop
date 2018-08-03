from opendrop.mvp.Presenter import Presenter
from opendrop.utility.events import handler

from ..base_config.model import ObserverConfigRequest

from .view import USBCameraConfigView


class USBCameraConfigPresenter(Presenter[ObserverConfigRequest, USBCameraConfigView]):
    DEFAULT_CAMERA_INDEX = 0

    def setup(self):
        self.model.type = self.view.OBSERVER_TYPE
        self.model.opts['camera_index'] = self.DEFAULT_CAMERA_INDEX

        self.view.set_camera_index(self.model.opts['camera_index'])

    @handler('view', 'on_camera_index_changed')
    def handle_camera_index_changed(self, index: int) -> None:
        self.model.opts['camera_index'] = index
