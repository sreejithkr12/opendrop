import asyncio
import itertools
import math
import time
import traceback
from enum import IntEnum
from math import cos, sin
from os.path import devnull
from typing import Optional, Tuple, Union, Iterable, IO, Callable

import numpy as np
from scipy import integrate, interpolate as sp_interpolate

from . import best_guess
from . import de
from .. import tolerances

last_paused = 0.0  # type: float
responsiveness = 0.015  # type: float


class FittingStopReason(IntEnum):
    CONVERGENCE_IN_PARAMETERS = 1
    CONVERGENCE_IN_GRADIENT   = 2
    CONVERGENCE_IN_OBJECTIVE  = 4
    MAXIMUM_STEPS_EXCEEDED    = 8

    @classmethod
    def str_from_num(cls, v: int) -> str:
        """Return a human-readable string representation of `v` (a flag field)."""
        present_flag_names = []

        for flag in cls:
            if v & flag == flag:
                present_flag_names.append(flag.name)

        return ' | '.join(present_flag_names)


def clamp(x, min_, max_):
    """Return `min_` if `x < min_`,
              `max_` if `x > max_` and
              `x`    if `min_ < x < max_`
    """
    return max(min_, min(x, max_))


# test for convergence in parameters
def convergence_in_parameters(scaled_delta):
    if abs(scaled_delta).max() < tolerances.DELTA_TOL:
        return FittingStopReason.CONVERGENCE_IN_PARAMETERS

    return 0


# test for convergence in gradient
def convergence_in_gradient(v):
    if abs(v).max() < tolerances.GRADIENT_TOL:
        return FittingStopReason.CONVERGENCE_IN_GRADIENT

    return 0


# test for convergence in objective function
def convergence_in_objective(objective):
    if objective < tolerances.OBJECTIVE_TOL:
        return FittingStopReason.CONVERGENCE_IN_OBJECTIVE

    return 0


# test maximum steps
def maximum_steps_exceeded(steps):
    if steps >= tolerances.MAXIMUM_FITTING_STEPS:
        return FittingStopReason.MAXIMUM_STEPS_EXCEEDED

    return 0


# test whether routine has converged
def trip_flags(scaled_delta, v, objective, steps):
    flags  = convergence_in_parameters(scaled_delta)
    flags |= convergence_in_gradient(v)
    flags |= convergence_in_objective(objective)
    flags |= maximum_steps_exceeded(steps)

    return flags


# the function g(s) used in finding the arc length for the minimal distance
def f_Newton(e_r, e_z, phi, dphi_ds, RP):
    f = - (e_r * cos(phi) + e_z * sin(phi)) / (RP + dphi_ds * (e_r * sin(phi) - e_z * cos(phi)))
    return f


class DoneFlag(IntEnum):
    CONVERGED = 1
    CANCELLED = 2
    ERROR = 4


class YoungLaplaceFit:
    PARAMETER_DIMENSIONS = 5

    # Contour must have coordinates with y-axis pointing upwards (opposite gravity).
    def __init__(self, contour: np.ndarray, log_file: IO = open(devnull, 'w')):
        # self.events = EventSource()  # type: EventSource

        self.contour = contour[contour[:, 1].argsort()]  # type: np.ndarray
        self.log_file = log_file

        self._done = False  # type: bool
        self._cancelled = False  # type: bool
        self.flags = 0  # type: DoneFlag

        self._params = None
        self._apex_rot_matrix = np.identity(2)

        # The theoretical profile of the drop based on the current estimated parameters.
        self._profile = None  # type: Optional[sp_interpolate.CubicSpline]
        self._profile_samples = 5000  # type: int
        self._profile_interpolation_limit = 4.0  # type: float
        self._profile_size = self._profile_interpolation_limit  # type: float

        # Levenberg–Marquardt–Fletcher (LMF)
        self._lmf_step = 0  # type: int

        self._objective = math.nan  # type: float
        self._residuals = None  # type: Optional[np.ndarray]

        async def do():
            try:
                # Guess the initial parameters.
                self.guess_contour()

                # Improve the initial guess and fit the parameters to the input contour data.
                stop_flags = await self.fit_contour()

                # Log that the fitting has finished.
                self.log()  # Log an empty line
                self.log('Fitting finished ({})'.format(FittingStopReason.str_from_num(stop_flags)))

                # Mark that this YoungLaplaceFit has converged.
                self.flags = DoneFlag.CONVERGED

            except FitCancelled:
                # Log that the fitting has been cancelled.
                self.log()
                self.log('Cancelled.')

                # Mark that this YoungLaplaceFit has been cancelled.
                self.flags = DoneFlag.CANCELLED

            except Exception as e:  # Unexpected error occurred in the fitting routine.
                # Log that an unexpected error has occurred.
                self.log()
                traceback.print_exception(type(e), e, tb=None, file=self.log_file)

                # Mark that this YoungLaplaceFit has stopped because of an unexpected error.
                self.flags = DoneFlag.ERROR
            finally:
                # Fitting is "done", i.e. is no longer progressing.
                self.mark_done()

        asyncio.get_event_loop().create_task(do())

    def log(self, *args, **kwargs):
        print(*args, **kwargs, file=self.log_file)

    # Initialises parameters to a first best guess
    def guess_contour(self):
        [apex_x, apex_y, apex_radius] = best_guess.fit_circle(self.contour)

        bond_number = best_guess.bond_number(self.contour, apex_x, apex_y, apex_radius)  # type: float

        omega_rotation = 0.0  # type: float

        self.params = [apex_x, apex_y, apex_radius, bond_number, omega_rotation]

    async def fit_contour(self) -> int:
        assert self.params is not None

        degrees_of_freedom = len(self.contour) - self.PARAMETER_DIMENSIONS + 1  # type: int

        ρ = 0.25  # type: float
        σ = 0.75  # type: float

        λ = 0  # type: float

        S_prev = None  # type: Optional[float]

        self.log('{: >4}  {: >10}  {: >10}  {: >10}  {: >11}  {: >10}  {:>11}'.format(
            'Step', 'Objective', 'x-centre', 'z-centre', 'Apex radius', 'Bond', 'Image angle'
        ))

        for self.lmf_step in itertools.count():
            await asyncio.sleep(0)

            A, v, S_next, residuals = await self.calculate_A_v_S()

            A_plus_λI = A + λ * np.diag(np.diag(A))

            A_plus_λI_inv = np.linalg.inv(A_plus_λI)

            delta = -(A_plus_λI_inv @ v).T

            if self.lmf_step > 0:
                R = (S_prev - S_next) / delta @ (-2 * v - (A.T @ delta.T))

                if R < ρ:  # Slow convergence
                    ν = clamp(2 - (S_next - S_prev) / delta @ v, min_=2, max_=10)

                    if λ == 0:
                        λ_c = 1 / abs(A_plus_λI_inv).max()
                        λ = λ_c

                        ν /= 2

                    λ *= ν
                elif R > σ:  # Rapid convergence
                    λ /= 2

                    if λ != 0 and λ < λ_c:  # todo: λ_c may not be defined yet?
                        λ = 0

            if S_prev is None or S_next < S_prev:  # if objective reduces accept (or if first run)
                self.params += delta[0]
                self.residuals = residuals
                self.objective = S_next / degrees_of_freedom
                S_prev = S_next

            # Log the fitting progress
            self.log('{: >4d} {: >11.4g} {: >11.4g} {: >11.4g}  {: >11.4g} {: >11.4g} {: >11.4g}°'.format(
                self.lmf_step, self.objective, *self.params[:-1], math.degrees(self.apex_rot)
            ))

            # Check if any fitting should stop.
            stop_flags = trip_flags(delta[0] / self.params, v, self.objective, self.lmf_step)
            if stop_flags:
                return stop_flags

    async def calculate_A_v_S(self):
        num_points = len(self.contour)  # type: int
        num_parameters = self.PARAMETER_DIMENSIONS  # type: int

        A = np.zeros((num_parameters, num_parameters))
        v = np.zeros((num_parameters, 1))

        residuals = np.zeros((num_points, 2))

        # ?
        s_left = 0.05 * self.profile_interpolation_limit
        s_right = 0.05 * self.profile_interpolation_limit

        s_max = 0

        for i, point in enumerate(self.contour):
            s_max = max(s_max, max(s_left, s_right))

            # Calculate the Jacobian and residual for each point
            jac_row_i, s_left, s_right, s_i, residual = await self.row_jacobian(*point, s_left, s_right)

            residuals[i] = s_i, residual

            # Since 'v' is a column array shape=(n, 1), can't just do v += jac_row_i * residual
            v[:, 0] += jac_row_i * residual

            # What operation does this do?
            for j in range(0, num_parameters):
                for k in range(0, j+1):
                    A[j][k] += jac_row_i[j] * jac_row_i[k]

        # todo: clean this up
        residuals[:, 0] = np.copysign(residuals[:, 0], self.contour[:, 0] - self.apex_x)

        self._profile_size = s_max

        # Mirror bottom triangle to top triangle
        A[np.triu_indices(num_parameters, 1)] = A.T[np.triu_indices(num_parameters, 1)]

        S = np.sum(residuals[:, 1]**2)

        return A, v, S, residuals

    # Calculates a Jacobian row for the data point xy = x, y
    async def row_jacobian(self, x, y, s_left, s_right):
        [xP, yP, RP, BP, wP] = self.params

        r, z = self.rz_from_xy(x - xP, y - yP)

        if r < 0:
            s_0 = s_left
        else:
            s_0 = s_right

        xs, ys, dx_dBs, dy_dBs, e_r, e_z, s_i = await self.minimum_arclength(r, z, s_0)  # functions at s*

        next_s_left = s_left
        next_s_right = s_right

        if r < 0:
            next_s_left = s_i
        else:
            next_s_right = s_i

        e_i = math.copysign(np.linalg.norm((e_r, e_z)), e_r)              # actual residual

        sign_r = math.copysign(1, r)  # calculates the sign for ddi_dX0

        ddi_dxP, ddi_dyP = -self.xy_from_rz(sign_r * e_r, e_z) / e_i
        # ddi_dxP = -( e_r * sgnx * cos(wP) + e_z * sin(wP) ) / e_i             # derivative w.r.t. X_0 (x at apex)
        # ddi_dyP = -(-e_r * sgnx * sin(wP) + e_z * cos(wP) ) / e_i             # derivative w.r.t. Y_0 (y at apex)

        ddi_dRP = -( e_r * xs + e_z * ys) / e_i  # derivative w.r.t. RP (apex radius)

        ddi_dBP = - RP * (e_r * dx_dBs + e_z * dy_dBs) / e_i   # derivative w.r.t. Bo  (Bond number)

        ddi_dwP = (e_r * sign_r * -z + e_z * r) / e_i
        # ddi_dwP = (e_r * sgnx * (- (x - xP) * sin(wP) - (y - yP) * cos(wP)) + e_z * ( (x - xP) * cos(wP) - (y - yP) * sin(wP))) / e_i

        return np.array([ ddi_dxP, ddi_dyP, ddi_dRP, ddi_dBP, ddi_dwP]), next_s_left, next_s_right, s_i, e_i

    # Calculate the minimum theoretical point to the point (r,z)
    async def minimum_arclength(self, r, z, s_i):
        xP, yP, RP, BP, wP = self.params

        r = abs(r)

        flag_bump = 0
        # f_i = 10000 # need to give this a more sensible value

        for step in range(tolerances.MAXIMUM_ARCLENGTH_STEPS):
            await self.housekeeping()

            xs, ys, phi_s, dx_dBs, dy_dBs, dphi_dBs = self.profile(s_i)

            e_r = r - RP * xs
            e_z = z - RP * ys
            # e_r = abs((x - xP) * cos(wP) - (y - yP) * sin(wP)) - RP * xs
            # e_z =    ((x - xP) * sin(wP) + (y - yP) * cos(wP)) - RP * ys

            dphi_ds = 2 - BP * ys - sin(phi_s) / xs

            s_next = s_i - f_Newton(e_r, e_z, phi_s, dphi_ds, RP)

            # f_iplus1 = RP * (e_r * cos(phi_s) + e_z * sin(phi_s))

            if s_next < 0:  # arc length outside integrated region
                s_next = 0
                flag_bump += 1

            if flag_bump >= 2:  # has already been pushed back twice - abort
                break

            if abs(s_next - s_i) < tolerances.ARCLENGTH_TOL:
                break

            # # this was to check if the residual was very small
            # if abs(f_iplus1 - f_i) < RESIDUAL_TOL:
            #     loop = False

            s_i = s_next

            # f_i = f_iplus1
        else:
            self.log('Warning: `minimum_arclength()` failed to converge in {} steps... (s_i = {:.4g})'
                     .format(tolerances.MAXIMUM_ARCLENGTH_STEPS, s_i))

        return xs, ys, dx_dBs, dy_dBs, e_r, e_z, s_i

    async def housekeeping(self, now: Callable[[], float] = time.time) -> None:
        global last_paused

        now = now()

        if now - last_paused > responsiveness:
            last_paused = now

            # Hand back control to the event loop to allow the GUI to remain responsive.
            await asyncio.sleep(0)

        # If something set `self._cancelled` to True, then raise a FitCancelled exception.
        if self._cancelled:
            raise FitCancelled

    def cancel(self) -> None:
        self._cancelled = True

    # interpolate the theoretical profile data, evaluating it at `s`, `s` can be one value or an array of values.
    def profile(self, s: Union[float, Iterable[float]]):
        if self._profile is None:
            raise ValueError(
                "Not all parameters have been specified, profile has not yet been generated"
            )

        try:
            s_min = min(s)
            s_max = max(s)
        except TypeError:
            s_min = s
            s_max = s

        if s_min < 0:
            raise ValueError('s-value outside domain, got {}'.format(s_min))

        # If the profile is called outside of the interpolated region, expand it by 20%.
        if s_max > self.profile_interpolation_limit:
            self.profile_interpolation_limit = 1.2 * s_max

        return self._profile(s)

    # generate a new drop profile
    def update_profile(self):
        if all(v is not None for v in (self.profile_interpolation_limit, self.profile_samples, self.params)):
            s_data = np.linspace(0, self.profile_interpolation_limit, self.profile_samples)

            # EPS = .000001 # need to use Bessel function Taylor expansion below
            x_vec_initial = [.000001, 0., 0., 0., 0., 0.]

            sampled_data = integrate.odeint(de.ylderiv, x_vec_initial, s_data, args=(self.bond,))

            # Boundary conditions for the spline
            bc = ((1, de.ylderiv(sampled_data[0], 0, self.bond)),
                  (1, de.ylderiv(sampled_data[-1], 0, self.bond)))

            # todo: make sure theoretical data is all finite, otherwise log the error and halt fit

            self._profile = sp_interpolate.CubicSpline(
                x=s_data, y=sampled_data, bc_type=bc
            )
        else:
            self._profile = None

    @property
    def params(self) -> Tuple:
        return tuple(self._params) if self._params is not None else None

    @params.setter
    def params(self, value: Tuple) -> None:
        if len(value) != self.PARAMETER_DIMENSIONS:
            raise ValueError(
                "Parameter array incorrect dimensions, expected {0}, got {1}"
                    .format(self.PARAMETER_DIMENSIONS, len(value))
            )

        self._params = value

        self.update_apex_rot_matrix()  # update wP rotation matrix
        self.update_profile()  # generate new profile when the parameters are changed

        # self.events.on_params_changed.fire()

    @property
    def profile_samples(self) -> int:
        return self._profile_samples

    @profile_samples.setter
    def profile_samples(self, value: int):
        if not value > 1:
            raise ValueError("Number of samples must be > 1, got {}".format(value))

        self._profile_samples = value

        self.update_profile()  # generate new profile when steps changed

    @property
    def profile_interpolation_limit(self) -> float:
        return self._profile_interpolation_limit

    @profile_interpolation_limit.setter
    def profile_interpolation_limit(self, value: float):
        if not value > 0:
            raise ValueError("Profile interpolation limit must be positive, got {}".format(value))

        self._profile_interpolation_limit = value

        self.update_profile()  # generate new profile when the maximum arc length is changed

    @property
    def profile_size(self) -> float:
        return self._profile_size

    @property
    def objective(self) -> float:
        return self._objective

    @objective.setter
    def objective(self, value: float) -> None:
        self._objective = value

        # self.events.on_objective_changed.fire()

    @property
    def lmf_step(self) -> int:
        return self._lmf_step

    @lmf_step.setter
    def lmf_step(self, value: int) -> None:
        self._lmf_step = value

        # self.events.on_lmf_step_changed.fire()

    @property
    def residuals(self) -> Optional[np.ndarray]:
        return self._residuals

    @residuals.setter
    def residuals(self, value: np.ndarray) -> None:
        self._residuals = value

        # self.events.on_residuals_changed.fire()

    @property
    def apex_x(self):
        return self.params[0]

    @property
    def apex_y(self):
        return self.params[1]

    @property
    def apex_radius(self):
        return self.params[2]

    @property
    def bond(self):
        return self.params[3]

    @property
    def apex_rot(self):
        return self.params[4]

    @property
    def apex_rot_matrix(self):
        return self._apex_rot_matrix

    def update_apex_rot_matrix(self):
        wP = self.apex_rot

        wP_matrix = np.array([
            [cos(wP), -sin(wP)],
            [sin(wP), cos(wP)]
        ])

        self._apex_rot_matrix = wP_matrix

    def rz_from_xy(self, x, y) -> np.ndarray:
        return self.apex_rot_matrix @ [x, y]

    def xy_from_rz(self, r, z) -> np.ndarray:
        return self.apex_rot_matrix.T @ [r, z]

    @property
    def done(self):
        return self._done

    def mark_done(self):
        self._done = True
        # self.events.on_done.fire()


class FitCancelled(Exception):
    pass
