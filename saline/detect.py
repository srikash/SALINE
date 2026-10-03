import numpy as np
from scipy.ndimage import laplace
from skimage.filters import frangi
from skimage import morphology


def detect_candidates(image, br_mask, csf, laplacian_threshold, frangi_threshold):
    """
    Detect electrode-track candidate voxels in `image` by combining a Laplacian-based
    edge mask and a Frangi vesselness mask, both restricted to `csf` and `br_mask`.

    Shared by both single- and dual-electrode segmentation: this step never differed
    between the two modes, only the line-fitting that follows it did.

    Returns (combined, lap, normalized_frangi):
      combined: the main candidate mask (frangi_img & lap).
      lap: the thresholded Laplacian mask alone, used by the laplacian-only fallback.
      normalized_frangi: the normalized Frangi response, re-thresholded by callers
        at a lower threshold if `combined` turns out too small.
    """
    brain_mask = morphology.isotropic_erosion(br_mask, radius=20)
    laplacian_filtered = laplace(image)
    pos = np.where(laplacian_filtered > 0, laplacian_filtered, 0)
    neg = -np.where(laplacian_filtered < 0, laplacian_filtered, 0)
    normalized_pos = pos / np.max(pos)
    normalized_neg = neg / np.max(neg)

    thresholded_pos = normalized_pos > laplacian_threshold
    thresholded_neg = normalized_neg > laplacian_threshold
    thresholded_img = thresholded_pos | thresholded_neg
    thresholded_img = thresholded_img.astype(np.uint8) * brain_mask.astype(np.uint8)
    thresholded_img = morphology.isotropic_closing(thresholded_img, radius=3)
    thresholded_img = morphology.remove_small_objects(thresholded_img, 5)
    thresholded_img = morphology.isotropic_dilation(thresholded_img, radius=2)
    lap = thresholded_img * csf

    brain_mask = morphology.isotropic_erosion(br_mask, radius=2)
    filtered = frangi(image)
    filtered = filtered * brain_mask.astype(np.uint8)
    min_val = np.min(filtered)
    max_val = np.max(filtered)
    normalized_frangi = (filtered - min_val) / (max_val - min_val)

    thresholded_image = normalized_frangi > frangi_threshold
    thresholded_image = morphology.isotropic_closing(thresholded_image, radius=3)
    thresholded_image = morphology.remove_small_objects(thresholded_image, 5)
    thresholded_image = morphology.isotropic_closing(thresholded_image, radius=8)
    thresholded_image = morphology.isotropic_dilation(thresholded_image, radius=2)
    frangi_img = thresholded_image * csf

    combined = frangi_img & lap
    return combined, lap, normalized_frangi
