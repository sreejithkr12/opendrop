from typing import Optional, List

import numpy as np
from matplotlib.figure import Figure


class DropFitFigureController:
    def __init__(self, figure: Figure):
        self.figure = figure  # type: Figure

        self._drop_image = None  # type: Optional[np.ndarray]
        self._drop_image_scale = 1  # type: Optional[float]
        self._drop_contour = None  # type: Optional[np.ndarray]
        self._drop_contour_fitted = None  # type: Optional[np.ndarray]

    def redraw(self) -> None:
        self.figure.clear()

        if self.drop_image is None:
            return

        extent = np.array([0, self.drop_image.shape[1], 0, self.drop_image.shape[0]]).astype(float)
        extent *= self.drop_image_scale

        axes = self.figure.add_subplot(1, 1, 1)
        axes.imshow(np.flipud(self.drop_image), origin='lower', extent=extent, aspect='equal')

        if self.drop_contour is None:
            return

        drop_contour = self.drop_contour.astype(float)
        drop_contour[:, 1] *= -1
        drop_contour[:, 1] += self.drop_image.shape[0]
        drop_contour *= self.drop_image_scale

        axes.plot(*zip(*drop_contour), linestyle='-', color='#0080ff', linewidth=1.5)

        if self.drop_contour_fitted is None:
            return

        drop_contour_fitted = self.drop_contour_fitted.astype(float)
        drop_contour_fitted[:, 1] *= -1
        drop_contour_fitted[:, 1] += self.drop_image.shape[0]
        drop_contour_fitted *= self.drop_image_scale

        axes.plot(*zip(*drop_contour_fitted), linestyle='-', color='#ff0080', linewidth=1)

        # Reset the limits as they may have been modified during the plotting of various lines
        axes.set_xlim(extent[:2])
        axes.set_ylim(extent[2:])

        if self.figure.canvas:
            self.figure.canvas.draw()

    @property
    def drop_image(self) -> Optional[np.ndarray]:
        return self._drop_image

    @drop_image.setter
    def drop_image(self, value: Optional[np.ndarray]) -> None:
        self._drop_image = value

        self.redraw()

    @property
    def drop_image_scale(self) -> float:
        return self._drop_image_scale

    @drop_image_scale.setter
    def drop_image_scale(self, value: float) -> None:
        self._drop_image_scale = value

        self.redraw()

    @property
    def drop_contour(self) -> Optional[np.ndarray]:
        return self._drop_contour.copy() if self._drop_contour is not None else None

    @drop_contour.setter
    def drop_contour(self, value: Optional[np.ndarray]) -> None:
        self._drop_contour = value

        self.redraw()

    @property
    def drop_contour_fitted(self) -> Optional[np.ndarray]:
        return self._drop_contour_fitted.copy() if self._drop_contour_fitted is not None else None

    @drop_contour_fitted.setter
    def drop_contour_fitted(self, value: Optional[np.ndarray]) -> None:
        self._drop_contour_fitted = value

        self.redraw()
