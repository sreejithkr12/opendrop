import functools

import numpy as np
from scipy import integrate

from . import de
from .young_laplace_fit import YoungLaplaceFit


# Memoize using a least-recently-used cache.
@functools.lru_cache()
def calculate_vol_sur(size: float, bond_number: float) -> np.ndarray:
    # EPS = .000001 # need to use Bessel function Taylor expansion below
    x_vec_initial = [.000001, 0., 0., 0., 0.]

    return integrate.odeint(
        de.dataderiv, x_vec_initial, t=[0, size], args=(bond_number,)
    )[-1][-2:]  # type: np.ndarray


# Calculate other properties derivable from a YoungLaplaceFit object and other physical parameters.
class YLDerivedProperties(object):
    def __init__(self, fit: YoungLaplaceFit, needle_width: float, drop_density: float, continuous_density: float,
                 gravity: float, pixel_to_mm: float):
        self.fit = fit  # type: YoungLaplaceFit
        self.needle_width = needle_width
        self.drop_density = drop_density  # type: float
        self.continuous_density = continuous_density  # type: float
        self.gravity = gravity  # type: float
        self.pixel_to_mm = pixel_to_mm  # type: float

    @property
    def ift(self) -> float:
        delta_density = abs(self.drop_density - self.continuous_density)
        bond_number = self.fit.bond
        apex_radius_m = self.fit.apex_radius * 1e-3 * self.pixel_to_mm  # 1e-3 convert mm to m

        gamma_ift_n = delta_density * self.gravity * apex_radius_m**2 / bond_number
        gamma_ift_mn = gamma_ift_n * 1e3  # 1e3 convert N to mN

        return gamma_ift_mn

    @property
    def volume(self) -> float:
        vol_sur = calculate_vol_sur(self.fit.profile_size, self.fit.bond)

        return vol_sur[0] * (self.fit.apex_radius*self.pixel_to_mm)**3

    @property
    def surface_area(self) -> float:
        vol_sur = calculate_vol_sur(self.fit.profile_size, self.fit.bond)

        return vol_sur[1] * (self.fit.apex_radius*self.pixel_to_mm)**2

    @property
    def worthington(self):
        delta_density = abs(self.drop_density - self.continuous_density)

        worthington_number = delta_density * self.gravity * self.volume*1e-9 / \
                             (np.pi * self.ift*1e-3 * self.needle_width*1e-3)

        return worthington_number

