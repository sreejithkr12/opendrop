import cv2
import numpy as np

from opendrop.image_filter.bases import ImageFilter
from opendrop.utility import data_binding
from opendrop.utility.events import EventSource, HasEvents


class CannyEdgeDetection(ImageFilter, HasEvents):
    def __init__(self, min_threshold: float = 30, max_threshold: float = 60):
        self.events = EventSource()  # type: EventSource

        self._min_threshold = min_threshold  # type: float
        self._max_threshold = max_threshold  # type: float

    def apply(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) > 2:
            image = cv2.cvtColor(image, code=cv2.COLOR_RGB2GRAY)

        image = cv2.Canny(image, self.min_threshold, self.max_threshold)

        image = cv2.cvtColor(image, code=cv2.COLOR_GRAY2RGB)

        return image

    @data_binding.property
    def min_threshold(self) -> float:
        return self._min_threshold

    @min_threshold.setter
    def min_threshold(self, value: float) -> None:
        self._min_threshold = value
        self._dirtied()

    @data_binding.property
    def max_threshold(self) -> float:
        return self._max_threshold

    @min_threshold.setter
    def max_threshold(self, value: float) -> None:
        self._max_threshold = value
        self._dirtied()

    def _dirtied(self) -> None:
        self.events.on_dirtied.fire()
