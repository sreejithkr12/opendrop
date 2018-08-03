from typing import Tuple

import cv2
import numpy as np

from opendrop.image_filter.bases import ImageFilter


class Crop(ImageFilter):
    def __init__(self, crop_region: Tuple[Tuple[float, float], Tuple[float, float]]):
        self.crop_region = np.array(crop_region)  # type: np.ndarray

    def apply(self, image: np.ndarray) -> np.ndarray:
        crop_region_px = (self.crop_region * image.shape[1::-1]).astype(int)
        crop_region_px.sort(axis=0)

        image = image[crop_region_px[0][1]:crop_region_px[1][1], crop_region_px[0][0]:crop_region_px[1][0]]

        return image
