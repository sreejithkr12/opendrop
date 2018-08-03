import cv2
import numpy as np

from opendrop.app2.imadjustments.base import Adjustment
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable


class CannyEdgeDetector(Adjustment):
    def __init__(self, min_threshold: float = 30, max_threshold: float = 60):
        self.bn_min_threshold = AtomicBindableVar(min_threshold)
        self.bn_max_threshold = AtomicBindableVar(max_threshold)

    def apply(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) > 2:  # If image is 3D (> 1 channel).
            image = cv2.cvtColor(image, code=cv2.COLOR_RGB2GRAY)

        # Perform Canny edge detection.
        image = cv2.Canny(image, self.min_threshold, self.max_threshold)

        # Convert back to three channel.
        image = cv2.cvtColor(image, code=cv2.COLOR_GRAY2RGB)

        return image

    @AtomicBindable.property_adapter
    def min_threshold(self): return self.bn_min_threshold

    @AtomicBindable.property_adapter
    def max_threshold(self): return self.bn_max_threshold
