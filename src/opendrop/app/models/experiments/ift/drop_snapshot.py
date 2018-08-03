import asyncio
from os.path import devnull
from typing import NewType, Tuple, Optional, List, IO

import cv2
import datetime
import numpy as np
import re

from opendrop.app.models.modifysettings import ModifySettings
from opendrop.app.settings import settings
from opendrop.mvp.Model import Model
from opendrop.image_filter.bases import ImageFilter
from opendrop.image_filter.crop import Crop
from opendrop.observer.bases import Observation, ObservationCancelled
from opendrop.utility import comvis, data_binding
from opendrop.utility.events import handler

from .young_laplace.young_laplace_fit import YoungLaplaceFit
from .young_laplace.young_laplace_fit import DoneFlag
from .young_laplace.yl_derived_properties import YLDerivedProperties

PointFloat2D = NewType('PointFloat2D', Tuple[float, float])
RectFloat = NewType('RectFloat', Tuple[PointFloat2D, PointFloat2D])


def save_to_camera_capture_history(image: np.ndarray) -> None:
    assert settings.camera_capture_history.enabled

    history_limit = settings.camera_capture_history.limit

    if history_limit <= 0:
        return

    parent = settings.camera_capture_history.location

    history = sorted((p for p in parent.iterdir() if p.is_file() and re.match(r'\d{8}_\d{6}_\d{6}\.[^\.]*$', p.name)),
                     reverse=True)
    for p in history[history_limit - 1:]:
        # todo: handle exceptions if fail to delete
        p.unlink()

    img_name = '{0.year:04}{0.month:02}{0.day:02}_{0.hour:02}{0.minute:02}{0.second:02}_{0.microsecond:06}' \
               .format(datetime.datetime.now())
    img_name += '.png'
    cv2.imwrite(str(parent/img_name), cv2.cvtColor(image, code=cv2.COLOR_BGR2RGB))

# todo: don't forward attributes from fit, have user access them directly, prop.fit.wait_until_not(None)
class DropSnapshot(Model):
    def __init__(self, observation: Observation, postproc: ImageFilter, drop_region: RectFloat, scale: float,
                 needle_width: float, inner_density: float, outer_density: float, gravity: float,
                 log_file: IO = open(devnull, 'w')):
        super().__init__()

        # status, Waiting for image, Fitting, Done, Image read failed, Fit failed
        self.done = False

        self._status = 'Waiting for image'  # type: str  # status.msg = messsage, status
        self._timestamp = None  # type: Optional[float]
        self._image = None  # type: Optional[np.ndarray]
        self._fit = None  # type: Optional[YoungLaplaceFit]
        self._drop_contour = None  # type: Optional[List[np.ndarray]]
        self._residuals = None
        self._extra = None  # type: Optional[YLDerivedProperties]

        self._log_file = log_file  # type: IO

        self.observation = observation
        self.postproc = postproc
        self.drop_region = drop_region
        self.scale = scale
        self.needle_width = needle_width
        self.inner_density = inner_density
        self.outer_density = outer_density
        self.gravity = gravity

        self.log = None

        async def await_observation():
            try:
                self.image = await observation
                if observation.volatile:
                    if settings.camera_capture_history.enabled:
                        save_to_camera_capture_history(self.image)

                self._timestamp = observation.timestamp
            except ObservationCancelled:
                self.status = 'Capture cancelled'

        asyncio.get_event_loop().create_task(await_observation())

    @property
    def sessile(self) -> bool:
        return self.inner_density < self.outer_density

    @data_binding.property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        self._status = value
        self.events.on_status_changed.fire()

    @data_binding.property
    def timestamp(self) -> float:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: float) -> None:
        self._timestamp = value

    @data_binding.property
    def image(self) -> np.ndarray:
        return self._image.copy() if self._image is not None else None

    @image.setter
    def image(self, value: np.ndarray) -> None:
        assert self.image is None

        self._image = value

        self.events.on_image_loaded.fire()

        self.begin_fit()

    @property
    def drop_image(self) -> np.ndarray:
        return Crop(self.drop_region).apply(self.image)

    @data_binding.property
    def drop_contour(self) -> Optional[List[np.ndarray]]:
        return self._drop_contour

    @drop_contour.setter
    def drop_contour(self, value: Optional[List[np.ndarray]]) -> None:
        self._drop_contour = value

        self.events.on_drop_contour_changed.fire()

    @property
    def drop_contour_fitted(self) -> Optional[List[np.ndarray]]:
        if self.fit is None or self.fit.params is None:
            return None

        true_profile_size = self.fit.profile_size  # type: float

        # Take the first two components only since these are the x, y coordinates and the rest are some other
        # parameters.
        contour_points = self.fit.profile(np.linspace(0, true_profile_size,  self.fit.profile_samples)
                                          ).T[:2]  # type: np.ndarray

        profile_left = [[-1, 0], [0, 1]] @ np.fliplr(contour_points)  # type: np.ndarray
        profile_right = contour_points  # type: np.ndarray

        profile = np.concatenate((profile_left, profile_right), axis=1)
        profile = np.array(self.fit.xy_from_rz(*profile))

        # Transform each point so that coordinates corresponds to the same pixel coordinates on the drop_image, to be
        # consistent with the coordinate space of `drop_contour`.

        profile *= self.fit.apex_radius
        profile += [self.fit.apex_x], [self.fit.apex_y]
        profile[1] *= -1

        if self.sessile:
           profile[1] *= -1

        #print('profile')
        #print(profile)

        return profile.T

    @property
    def fit(self) -> YoungLaplaceFit:
        return self._fit

    @fit.setter
    def fit(self, value: YoungLaplaceFit) -> None:
        assert self.fit is None

        self._fit = value
        self._extra = YLDerivedProperties(value, self.needle_width, self.inner_density, self.outer_density,
                                          self.gravity, self.scale)

        self.fit.events.connect_handlers(self, 'fit')

    @property
    def derived(self) -> YLDerivedProperties:
        assert self.fit is not None

        return self._extra

    @property
    def log_file(self) -> IO:
        return self._log_file

    @log_file.setter
    def log_file(self, value: IO) -> None:
        self._log_file = value

        if self.fit is not None:
            self.fit.log_file = self._log_file

    # YoungLaplaceFit parameters
    @data_binding.property
    def apex_x(self):
        if self.fit.params is None:
            raise AttributeError

        return self.fit.params[0]

    @data_binding.property
    def apex_y(self):
        if self.fit.params is None:
            raise AttributeError

        return [-1, 1][self.sessile] * self.fit.params[1]

    @data_binding.property
    def apex_radius(self):
        if self.fit.params is None:
            raise AttributeError

        return self.fit.params[2]

    @data_binding.property
    def bond(self):
        if self.fit.params is None:
            raise AttributeError

        return self.fit.params[3]

    @data_binding.property
    def apex_rot(self):
        if self.fit.params is None:
            raise AttributeError

        return [-1, 1][self.sessile] * self.fit.params[4]

    @data_binding.property
    def residuals(self):
        if self.fit is None:
            raise AttributeError

        return self.fit.residuals

    def begin_fit(self) -> None:
        assert self.image is not None

        self.status = 'Fitting'

        image = self.image
        image = self.postproc.apply(Crop(self.drop_region).apply(image))

        if len(image.shape) > 2:
            image = cv2.cvtColor(image, code=cv2.COLOR_RGB2GRAY)

        self.drop_contour = comvis.squish_contour(comvis.find_contours(image)[0])

        # # Visualizing curves
        # im = np.copy(self.image)
        # for i, p in enumerate(self.drop_contour):
        #     im[tuple(p[::-1])] = np.array(hsv_to_rgb(i/(len(self.drop_contour)), 1, 1)[::-1])*255
        # cv2.imshow('asg', im)
        # cv2.waitKey(0)

        drop_contour = np.copy(self.drop_contour)
        if self.sessile:
            # Sessile drop, flip the contours
            drop_contour[:, 1] *= -1

        # Flip the contour since YoungLaplaceFit expects +y to be upwards (relative to gravity).
        drop_contour[:, 1] *= -1
        self.fit = YoungLaplaceFit(drop_contour, log_file=self.log_file)

    @handler('fit', 'on_params_changed', immediate=True)
    def handle_fit_params_changed(self) -> None:
        data_binding.poke(self, type(self).apex_x)
        data_binding.poke(self, type(self).apex_y)
        data_binding.poke(self, type(self).apex_radius)
        data_binding.poke(self, type(self).bond)
        data_binding.poke(self, type(self).apex_rot)

        data_binding.poke(self, type(self).drop_contour)

        self.events.on_params_changed.fire()

    @handler('fit', 'on_residuals_changed')
    def handle_fit_residuals_changed(self) -> None:
        self.events.on_residuals_changed.fire()

    @handler('fit', 'on_done')
    def handle_fit_converged(self) -> None:
        if self.fit.flags & DoneFlag.CONVERGED == DoneFlag.CONVERGED:
            self.status = 'Done'
        elif self.fit.flags & DoneFlag.CANCELLED == DoneFlag.CANCELLED:
            self.status = 'Fitting cancelled'
        elif self.fit.flags & DoneFlag.ERROR == DoneFlag.ERROR:
            self.status = 'Error in fitting'
        else:
            self.status = 'unknown'

        self.done = True
