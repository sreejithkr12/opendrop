import cv2
import numpy as np

from opendrop.image_filter.bases import ImageFilter


class GaussianBlur(ImageFilter):
    def __init__(self, blur_size: int):
        # Blur size must be odd for cv2.GaussianBlur
        self.blur_size = round(blur_size/2)*2 + 1

    def apply(self, image: np.ndarray) -> np.ndarray:
        image = cv2.GaussianBlur(image, (self.blur_size, self.blur_size), 0)

        return image
