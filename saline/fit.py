import numpy as np
from skimage import morphology
from sklearn.linear_model import RANSACRegressor


def fit_best_fit_line_RANSAC(points):
    X = points[:, :2]  # Use the first two coordinates (x, y) as features
    y = points[:, 2]   # Use the third coordinate (z) as the target

    ransac = RANSACRegressor(min_samples=2, random_state=42, loss='absolute_error')
    ransac.fit(X, y)

    inlier_points = points[ransac.inlier_mask_]
    centroid = np.mean(inlier_points, axis=0)
    centered_points = inlier_points - centroid
    _, _, vt = np.linalg.svd(centered_points)
    direction = vt[0]

    return centroid, direction


def fit_best_fit_line(points):
    centroid = np.mean(points, axis=0)
    centered_points = points - centroid
    _, _, vt = np.linalg.svd(centered_points)
    direction = vt[0]

    return centroid, direction


def draw_lines(ends, img_shape, fits, br_mask, radius=6):
    """
    Draw one dilated binary mask covering every region's fitted line.

    Args:
        ends: per-region starting slice index, same length as `fits` (length 1 for
            single-electrode, length 2 for dual-electrode: left end, right end).
        img_shape: shape of the 3D volume, used to keep points in bounds.
        fits: per-region (centroid, direction) tuples, one per region.
        br_mask: brain mask the result is multiplied by before dilation.
        radius: dilation radius applied to the final mask.

    Returns:
        A binary mask with ones along every region's line, dilated by `radius`.
    """
    step = 0.1
    final_result = np.zeros(img_shape)

    for end, (centroid, direction) in zip(ends, fits):
        z = np.arange(end, img_shape[-1], step)
        # k is the scalar in the line definition equation (point = centroid + k * direction)
        k = (z - centroid[-1]) / direction[-1]
        elec = np.floor(centroid + np.outer(k, direction)).astype(int)

        cond = (elec[:, 0] > 0) & (elec[:, 0] < img_shape[0]) & \
               (elec[:, 1] > 0) & (elec[:, 1] < img_shape[1]) & \
               (elec[:, 2] > 0) & (elec[:, 2] < img_shape[2])
        final_result[tuple(elec[cond].T)] = 1

    final_result = final_result * br_mask
    final_result = morphology.isotropic_dilation(final_result, radius=radius)
    return final_result
