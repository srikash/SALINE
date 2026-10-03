import numpy as np
from skimage import morphology

from .detect import detect_candidates
from .fit import fit_best_fit_line, fit_best_fit_line_RANSAC, draw_lines

CSF_EXCLUDED_LABELS = (24, 4, 43, 44, 5, 15)  # SynthSeg labels for CSF / excluded structures
VENTRAL_DC_LABELS = (28, 60)  # left, right VentralDC: electrode track ends near its base


def _electrode_ends(seg, num_regions):
    _, __, left_end = np.min(np.transpose(np.nonzero(seg == VENTRAL_DC_LABELS[0])), axis=0)
    _, __, right_end = np.min(np.transpose(np.nonzero(seg == VENTRAL_DC_LABELS[1])), axis=0)
    if num_regions == 1:
        return (max(left_end, right_end) + 5,)
    return (left_end + 5, right_end + 5)


def _region_points(mask, num_regions):
    """Split `mask` into left/right halves for dual-electrode mode, or take it whole."""
    if num_regions == 1:
        return [np.transpose(np.nonzero(mask))]
    half = mask.shape[0] // 2
    left = np.zeros_like(mask)
    right = np.zeros_like(mask)
    left[:half, :, :] = mask[:half, :, :]
    right[half:, :, :] = mask[half:, :, :]
    return [np.transpose(np.nonzero(left)), np.transpose(np.nonzero(right))]


def _regions_have_spread(points_list, axis, min_spread):
    if any(pts.shape[0] == 0 for pts in points_list):
        return False
    for pts in points_list:
        spread = pts[:, axis].max() - pts[:, axis].min()
        if spread < min_spread:
            return False
    return True


def _fit_regions_with_ransac_check(points_list):
    """Fallback-path fit: use RANSAC when points look like they contain outliers."""
    fits = []
    for pts in points_list:
        y_spread = pts[:, 1].max() - pts[:, 1].min()
        if y_spread > 30:
            fits.append(fit_best_fit_line_RANSAC(pts))
        else:
            fits.append(fit_best_fit_line(pts))
    return fits


def segment(image, br_mask, seg, num_regions,
            laplacian_threshold, frangi_threshold, lower_frangi_threshold,
            save_intermediate=None):
    """
    Segment one (num_regions=1) or two (num_regions=2, left/right split) electrode
    tracks in `image`.

    Args:
        image, br_mask, seg: np.ndarray volumes — the subject MRI, its brain mask,
            and its SynthSeg label volume.
        num_regions: 1 for single-electrode mode, 2 for dual-electrode mode.
        laplacian_threshold, frangi_threshold, lower_frangi_threshold: detection
            thresholds (see `detect.detect_candidates`).
        save_intermediate: optional `callback(name, mask)` invoked with each
            intermediate mask that's worth persisting, so this function stays
            array-in/array-out and callers decide whether/how to save to disk.

    Returns:
        A binary mask (np.ndarray) covering the detected electrode track(s), or
        None if no candidate voxels could be found even after both fallbacks.
    """
    csf = np.ones(seg.shape, dtype=bool)
    for label in CSF_EXCLUDED_LABELS:
        csf &= (seg != label)
    csf = morphology.isotropic_erosion(csf, radius=3)

    ends = _electrode_ends(seg, num_regions)

    combined, lap, normalized_frangi = detect_candidates(
        image, br_mask, csf, laplacian_threshold, frangi_threshold)

    if save_intermediate:
        save_intermediate("thr-lap", lap)
        save_intermediate("comb", combined)

    points = _region_points(combined, num_regions)

    if _regions_have_spread(points, axis=2, min_spread=10):
        fits = [fit_best_fit_line(pts) for pts in points]
    else:
        print("ah oh, frangi only now. Lowering threshold...")
        frangi_img = normalized_frangi > lower_frangi_threshold
        frangi_img = frangi_img * csf
        frangi_img = morphology.isotropic_closing(frangi_img, radius=3)
        frangi_img = morphology.remove_small_objects(frangi_img, 5)
        if save_intermediate:
            save_intermediate("frangi", frangi_img)
        points = _region_points(frangi_img, num_regions)

        if any(pts.shape[0] == 0 for pts in points):
            print("ah oh, frangi only didn't work. Trying laplacian only...")
            points = _region_points(lap, num_regions)
            if any(pts.shape[0] == 0 for pts in points):
                print("OH NO, laplacian only still didn't work... SKIP")
                return None

        fits = _fit_regions_with_ransac_check(points)

    return draw_lines(ends, image.shape, fits, br_mask)
