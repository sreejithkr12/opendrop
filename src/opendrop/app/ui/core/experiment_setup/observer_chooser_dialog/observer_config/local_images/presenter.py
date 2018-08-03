from typing import Tuple

from opendrop.mvp.Presenter import Presenter
from opendrop.utility.events import handler

from ..base_config.model import ObserverConfigRequest

from .view import ImagesConfigView


class ImagesConfigPresenter(Presenter[ObserverConfigRequest, ImagesConfigView]):
    def setup(self):
        self.model.type = self.view.OBSERVER_TYPE

        self._frame_interval = 10  # type: int

        self.model.opts['image_paths'] = tuple() #['/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image0.png', '/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image1.png', '/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image2.png', '/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image3.png', '/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image4.png']
                                         # tuple()
        self.model.opts['timestamps'] = []

        self.view.set_frame_interval_input(self.frame_interval)

    def update_model_timestamps(self):
        self.model.opts['timestamps'] = [i * self.frame_interval for i in range(len(self.model.opts['image_paths']))]

    @handler('view', 'on_file_input_changed')
    def handle_file_input_changed(self, filenames: Tuple[str]) -> None:
        self.model.opts['image_paths'] = [*sorted(filenames)]

        self.update_model_timestamps()

    @handler('view', 'on_frame_interval_input_changed')
    def handle_on_frame_interval_input_changed(self, interval: int) -> None:
        self.frame_interval = interval

    @property
    def frame_interval(self) -> int:
        return self._frame_interval

    @frame_interval.setter
    def frame_interval(self, value: int) -> None:
        self._frame_interval = value

        self.update_model_timestamps()
