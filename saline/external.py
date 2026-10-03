"""Runs the external tools SALINE's standalone pipeline needs: ANTs
(resampling, N4 bias correction, mask multiply), SynthStrip, and SynthSeg.

Docker is tried first for all three, since it needs no local install:
  - ANTs:       https://hub.docker.com/r/antsx/ants
  - SynthStrip: https://hub.docker.com/r/freesurfer/synthstrip
  - SynthSeg:   https://hub.docker.com/r/cookpa/synthseg

ANTs falls back to a local install (`ResampleImage`/`N4BiasFieldCorrection`/
`ImageMath` on PATH) if Docker isn't available, since there's no other
precomputed file a caller could hand in for a resampling step. SynthStrip
and SynthSeg have no such local fallback here -- if Docker isn't available,
the caller (pipeline.preprocess) expects a precomputed brain mask or
segmentation instead.

Every path handed to a container is resolved to an absolute path first: the
container's working directory is not the caller's cwd, so a relative path
like `saline --input subject.nii.gz` would otherwise mount the right
directory but still fail to find the file by its relative name inside it.
"""

import os
import shutil
import subprocess

ANTS_DOCKER_IMAGE = os.environ.get("SALINE_ANTS_IMAGE", "antsx/ants:latest")
SYNTHSTRIP_DOCKER_IMAGE = os.environ.get("SALINE_SYNTHSTRIP_IMAGE", "freesurfer/synthstrip:1.8")
SYNTHSEG_DOCKER_IMAGE = os.environ.get("SALINE_SYNTHSEG_IMAGE", "cookpa/synthseg:conda-0.2")


class ExternalToolError(RuntimeError):
    pass


def docker_available():
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, check=True,
        )
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def _run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise ExternalToolError(
            f"command failed ({result.returncode}): {' '.join(cmd)}\n{result.stdout}"
        )


def _run_in_docker(image, args):
    """`args` must already be absolute paths (see module docstring) mixed with
    plain string flags/values; only `str` entries that are existing parent
    directories matter for mounting, so callers pass the full arg list and we
    mount every absolute path's parent directory found in it."""
    dirs = sorted({os.path.dirname(a) for a in args if a.startswith("/")})
    mounts = []
    for d in dirs:
        mounts += ["-v", f"{d}:{d}"]
    cmd = [
        "docker", "run", "--rm",
        "-u", f"{os.getuid()}:{os.getgid()}",
        *mounts, image, *args,
    ]
    _run(cmd)


def resample_to_iso(input_path, output_path, spacing="1.0x1.0x1.0"):
    """Resample `input_path` to isotropic `spacing` mm, windowed-sinc (Lanczos)
    interpolated -- suitable for a continuous-intensity MRI, not a label mask."""
    input_path = os.path.realpath(input_path)
    output_path = os.path.realpath(output_path)
    args = ["ResampleImage", "3", input_path, output_path, spacing, "0", "3[l]"]
    if docker_available():
        _run_in_docker(ANTS_DOCKER_IMAGE, args)
    elif shutil.which("ResampleImage"):
        _run(args)
    else:
        raise ExternalToolError(
            "Neither Docker nor a local ResampleImage (ANTs) was found. "
            "Install Docker, or install ANTs locally."
        )


def resample_to_native(input_path, output_path, native_shape):
    """Resample a label/mask volume at `input_path` to `native_shape`
    (a (d1, d2, d3) voxel-count tuple), nearest-neighbor interpolated so
    binary values aren't blurred."""
    input_path = os.path.realpath(input_path)
    output_path = os.path.realpath(output_path)
    size = "x".join(str(int(d)) for d in native_shape)
    args = ["ResampleImage", "3", input_path, output_path, size, "1", "1"]
    if docker_available():
        _run_in_docker(ANTS_DOCKER_IMAGE, args)
    elif shutil.which("ResampleImage"):
        _run(args)
    else:
        raise ExternalToolError(
            "Neither Docker nor a local ResampleImage (ANTs) was found. "
            "Install Docker, or install ANTs locally."
        )


def n4_correct(input_path, mask_path, output_path):
    input_path = os.path.realpath(input_path)
    mask_path = os.path.realpath(mask_path)
    output_path = os.path.realpath(output_path)
    args = ["N4BiasFieldCorrection", "-d", "3", "-x", mask_path, "-i", input_path, "-o", output_path]
    if docker_available():
        _run_in_docker(ANTS_DOCKER_IMAGE, args)
    elif shutil.which("N4BiasFieldCorrection"):
        _run(args)
    else:
        raise ExternalToolError(
            "Neither Docker nor a local N4BiasFieldCorrection (ANTs) was found. "
            "Install Docker, or install ANTs locally."
        )


def mask_multiply(output_path, image_path, mask_path):
    """output = image * mask, i.e. a skull-stripped image given a brain mask."""
    output_path = os.path.realpath(output_path)
    image_path = os.path.realpath(image_path)
    mask_path = os.path.realpath(mask_path)
    args = ["ImageMath", "3", output_path, "m", image_path, mask_path]
    if docker_available():
        _run_in_docker(ANTS_DOCKER_IMAGE, args)
    elif shutil.which("ImageMath"):
        _run(args)
    else:
        raise ExternalToolError(
            "Neither Docker nor a local ImageMath (ANTs) was found. "
            "Install Docker, or install ANTs locally."
        )


def synthstrip(input_path, stripped_out, mask_out):
    if not docker_available():
        raise ExternalToolError(
            "Docker isn't available to run SynthStrip. "
            "Install Docker, or pass a precomputed brain mask instead."
        )
    input_path = os.path.realpath(input_path)
    stripped_out = os.path.realpath(stripped_out)
    mask_out = os.path.realpath(mask_out)
    args = ["-i", input_path, "-o", stripped_out, "-m", mask_out]
    _run_in_docker(SYNTHSTRIP_DOCKER_IMAGE, args)


def synthseg(input_path, seg_out, threads=5):
    if not docker_available():
        raise ExternalToolError(
            "Docker isn't available to run SynthSeg. "
            "Install Docker, or pass a precomputed segmentation instead."
        )
    input_path = os.path.realpath(input_path)
    seg_out = os.path.realpath(seg_out)
    args = ["--i", input_path, "--o", seg_out, "--threads", str(threads), "--cpu"]
    _run_in_docker(SYNTHSEG_DOCKER_IMAGE, args)
