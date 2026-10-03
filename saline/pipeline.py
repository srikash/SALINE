import os
import shutil

from . import external
from .volume import get_shape


def derive_base(input_path):
    """Strip the .nii/.nii.gz suffix, e.g. '/a/b/subject.nii.gz' -> '/a/b/subject'."""
    idx = input_path.find(".nii")
    return input_path[:idx] if idx != -1 else input_path


def _copy_if_distinct(src, dst):
    """shutil.copy, but a no-op when src already *is* dst (e.g. the caller's
    override file happens to sit at the pipeline's own derived path)."""
    if os.path.realpath(src) != os.path.realpath(dst):
        shutil.copy(src, dst)


def preprocess(raw_input_path, brain_mask_override=None, synthseg_override=None,
                threads=5, on_stage=None):
    """
    Run the full SALINE preprocessing pipeline on a raw, native-space clinical
    MRI: resample to 1mm isotropic, skull-strip (SynthStrip), N4 bias correct,
    segment (SynthSeg). SynthStrip and SynthSeg run via Docker by default; pass
    `brain_mask_override` / `synthseg_override` (paths to precomputed files,
    already in 1mm-isotropic space) to skip either step, e.g. when Docker isn't
    available.

    Returns a dict with the paths of every file produced (including the
    retained 1mm-isotropic MRI) and `native_shape`, the original volume's
    voxel shape, needed to resample results back to native space afterward.
    """
    on_stage = on_stage or (lambda message: None)
    base = derive_base(raw_input_path)

    native_shape = get_shape(raw_input_path)

    iso_path = f"{base}_1mm_iso.nii.gz"
    stripped_path = f"{base}_1mm_iso_skull_striped.nii.gz"
    mask_path = f"{base}_1mm_iso_brain_mask.nii.gz"
    n4_path = f"{base}_1mm_iso_skull_striped_n4.nii.gz"
    seg_path = f"{base}_1mm_iso_skull_striped_n4_seg.nii.gz"

    on_stage("Resampling to 1mm isotropic")
    external.resample_to_iso(raw_input_path, iso_path)

    if brain_mask_override:
        on_stage("Using provided brain mask")
        _copy_if_distinct(brain_mask_override, mask_path)
        external.mask_multiply(stripped_path, iso_path, mask_path)
    else:
        on_stage("Running SynthStrip")
        external.synthstrip(iso_path, stripped_path, mask_path)

    on_stage("N4 bias correction")
    external.n4_correct(stripped_path, mask_path, n4_path)

    if synthseg_override:
        on_stage("Using provided SynthSeg segmentation")
        _copy_if_distinct(synthseg_override, seg_path)
    else:
        on_stage("Running SynthSeg")
        external.synthseg(n4_path, seg_path, threads=threads)

    return {
        "base": base,
        "native_shape": native_shape,
        "iso": iso_path,
        "stripped": stripped_path,
        "brain_mask": mask_path,
        "n4": n4_path,
        "synthseg": seg_path,
    }
