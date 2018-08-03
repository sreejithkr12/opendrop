import cv2
import numpy as np

from opendrop.image_filter.bases import ImageFilter


class Dilate(ImageFilter):
    def __init__(self, size: int):
        self.size = size

    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.dilate(image, np.ones((self.size, self.size)))

        return image
