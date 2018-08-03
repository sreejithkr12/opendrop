import itertools

import cv2
import numpy as np

from opendrop.utility import comvis

NEEDLE_TOL   = 1.e-4
NEEDLE_STEPS = 20


def needle_diameter_from_image(needle_image: np.ndarray) -> float:
    """Return the diameter of the needle given by the image `needle_image` by first using `comvis.detect_edges()` to
    extract the `needle_profile`.

    If the image passed isn't single channel or binary, then `needle_image` is first converted to gray scale, and using
    `cv2.Canny()`, the image is converted to binary with `threshold2` equal to `comvis.otsu_threshold_val(needle_image)`
    and `threashold1=threshold2/2`.
    """
    if needle_image.size == 0:
        raise ValueError('`needle_image` is an empty array')

    if len(needle_image.shape) > 2:
        # assume image is in RGB format
        needle_image = cv2.cvtColor(needle_image, code=cv2.COLOR_RGB2GRAY)

    pixel_values = np.unique(needle_image)  # type: np.ndarray

    if len(pixel_values) > 2 or not(pixel_values == [0, 1]).all():
        otsu_val = comvis.otsu_threshold_val(needle_image)
        needle_image = cv2.Canny(needle_image, threshold1=otsu_val/2, threshold2=otsu_val)

    needle_profile = comvis.find_contours(needle_image)[:2]

    return needle_diameter(needle_profile)


def needle_diameter(needle_profile: np.ndarray):
    """Return the diameter of the needle defined by `needle_profile`

    :param needle_profile: The two edges of the needle, this is an `np.ndarray` in the format:
                               [[[x0, y0], ..., [xn, yn]], [[x'0, y'0], ..., [x'm, y'm]]]
                           Where xi, yi correspond to the left edge of the needle and x'i, y'i, the right edge.
    :return: Diameter of the needle (in same units as `needle_profile`)
    """
    if len(needle_profile) != 2:
        raise ValueError(
            '`needle_profile` must contain only two contours (left and right edge of needle), got `{}` contour(s)'
            .format(len(needle_profile))
        )

    needle_profile = np.array([edge[edge[:, 1].argsort()] for edge in needle_profile])

    p0 = needle_profile[0][0]

    # Set top left point of needle_profile to (0, 0)
    needle_profile -= p0

    [x0, x1, theta] = optimise_needle(needle_profile)

    needle_diameter = abs((x1 - x0) * np.sin(theta))

    return needle_diameter


def optimise_needle(needle_profile: np.ndarray) -> np.ndarray:
    """

    :param needle_profile: The two edges of the needle, see `needle_diameter()` doc
    :return: [x0, x1, theta] where:
                 x0: needle left edge x-coordinate.
                 x1: needle right edge x-coordinate.
                 theta: angle of needle in radians (theta) where 0 is horizontal.
    """
    edge0 = needle_profile[0]
    edge1 = needle_profile[1]

    # First guess
    x0 = edge0[0][0]
    x1 = edge1[0][0]

    theta = np.pi/2

    params = np.array([x0, x1, theta])

    for step in itertools.count():
        residuals, jac = build_resids_jac(needle_profile, *params)

        jtj = np.dot(jac.T, jac)
        jte = np.dot(jac.T, residuals)

        delta = -np.dot(np.linalg.inv(jtj), jte).T

        params += delta

        if (abs(delta/params) < NEEDLE_TOL).all() or step > NEEDLE_STEPS:
            break

    return params


def build_resids_jac(needle_profile, x0, x1, theta):
    edge0, edge1 = needle_profile

    edge0_res, edge0_jac = edge_resids_jac(edge0, x0, theta)
    edge1_res, edge1_jac = edge_resids_jac(edge1, x1, theta)

    residuals = np.hstack((edge0_res, edge1_res))

    num_points = edge0_jac.shape[0] + edge1_jac.shape[0]

    jac = np.zeros((num_points, 3))

    jac[:len(edge0_jac), :2] = edge0_jac
    jac[len(edge0_jac):, 0] = edge1_jac[:, 0]
    jac[len(edge0_jac):, 2] = edge1_jac[:, 1]

    return [residuals, jac]


def edge_resids_jac(edge, x0, theta):
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)

    residuals = np.array([(point[0] - x0) * sin_theta - point[1] * cos_theta for point in edge])

    jac = np.array([
        [-sin_theta, (point[0] - x0) * cos_theta + point[1] * sin_theta] for point in edge
    ])

    return [residuals, jac]
