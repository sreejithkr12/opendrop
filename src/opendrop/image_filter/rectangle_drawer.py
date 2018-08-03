from typing import NewType, Tuple

import cv2
import numpy as np

from opendrop.image_filter.bases import ImageFilter
from opendrop.utility import data_binding
from opendrop.utility.events import Event

RGB = NewType('RGB', Tuple[int, int, int])


class RectangleDrawer(ImageFilter):
    class _Events:
        def __init__(self):
            self.on_dirtied = Event()

    def __init__(self, color: RGB, thickness: int = 1):
        self.events = self._Events()

        self._color = color  # type: RGB
        self.thickness = thickness  # type: int

        self._rect = ((0, 0), (0, 0))  # type: Tuple[Tuple[float, float], Tuple[float, float]]

    @data_binding.property
    def rect(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        return self._rect

    @rect.setter
    def rect(self, value: Tuple[Tuple[float, float], Tuple[float, float]]) -> None:
        self._rect = value

        self._dirtied()

    @property
    def color(self) -> RGB:
        return self._color

    @color.setter
    def color(self, value: RGB) -> None:
        self._color = value

        self._dirtied()

    @property
    def p0(self) -> Tuple[float, float]:
        return self.rect[0]

    @property
    def p1(self) -> Tuple[float, float]:
        return self.rect[1]

    def apply(self, image: np.ndarray) -> np.ndarray:
        rect_px = tuple(tuple((p * np.flip(image.shape[:2], 0)).astype(int)) for p in self.rect)

        if rect_px[1][0] - rect_px[0][0] == 0 and rect_px[1][1] - rect_px[0][1] == 0:
            return image

        return cv2.rectangle(img=image, pt1=rect_px[0], pt2=rect_px[1], color=self.color, thickness=self.thickness)

    def _dirtied(self) -> None:
        self.events.on_dirtied.fire()
