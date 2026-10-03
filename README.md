# SALINE (part of DBS-ElecNet)
## <b><ins>S</ins></b>egmentation <b><ins>A</ins></b>lgorithm using <b><ins>LIN</ins></b>e-fitting for <b><ins>E</ins></b>lectrodes

*V. H. Yu et al., "DBS-ElecNet: Automated Localization and Segmentation of DBS Electrodes in Clinical MRI," 2026 IEEE 23rd International Symposium on Biomedical Imaging (ISBI), London, United Kingdom, 2026, pp. 1-4, doi:[10.1109/ISBI61048.2026.11515562](https://doi.org/10.1109/ISBI61048.2026.11515562)*

Give SALINE a raw clinical T1-weighted MR image and it handles the rest: resampling, 
skull-stripping (SynthStrip), bias correction (N4), and segmentation (SynthSeg) 
all run via Docker, with no other install needed. It runs as a fully standalone CLI tool.

It is the core of [DBS-ElecNet](https://github.com/BRAIN-TO/DBS-ElecNet)'s 
classical (non-deep-learning) segmentation pipeline.

## Why SALINE?

SALINE is a classical, filtering-based automatic segmentation method for DBS
electrodes: no training, no manual annotation, no GPU. Give it an MRI, a brain
mask, and a SynthSeg segmentation, and it finds the electrode track with a
Laplacian/Frangi filter cascade and a line fit.

That makes it well suited to building a large database of electrode
segmentations, at scale, without a human labeling each scan by hand. In the
DBS-ElecNet paper, SALINE segmented 280 post-operative MRI scans in about 1.5
minutes each, and those segmentations became the training data for
DBS-ElecNet's 3D U-Net. Any similar segmentation model can be trained the
same way: run SALINE over a cohort, use its output as ground truth.

## Install

Requires Python 3.12+ and [Docker](https://www.docker.com) (recommended — see
below for running without it).

```bash
pip install git+https://github.com/srikash/SALINE.git@v0.3.0
```

## Usage

Dual-electrode (default — also available explicitly as `saline dual`):

```bash
saline --input subject.nii.gz
```

Single-electrode:

```bash
saline single --input subject.nii.gz
```

`--input` is a raw, native-space clinical MRI. SALINE resamples it to 1mm
isotropic, skull-strips it (SynthStrip), bias-corrects it (N4), and segments
it (SynthSeg) before finding the electrode track — all via Docker, pulling
[`antsx/ants`](https://hub.docker.com/r/antsx/ants),
[`freesurfer/synthstrip`](https://hub.docker.com/r/freesurfer/synthstrip), and
[`cookpa/synthseg`](https://hub.docker.com/r/cookpa/synthseg) on first use.

**Output:**

* `subject_saline_elecSeg.nii.gz`: the electrode segmentation, in `--input`'s native space.
* `subject_1mm_iso.nii.gz`: the resampled MRI, kept for reference.
* `subject_1mm_iso_saline_elecSeg.nii.gz`: the electrode segmentation, in 1mm-isotropic space.

**Running without Docker:**

If Docker isn't available, pass precomputed files instead — both must already
be in the same 1mm-isotropic space as `subject_1mm_iso.nii.gz`:

* `--brain_mask PATH`: skips Docker-based SynthStrip.
* `--synthseg PATH`: skips Docker-based SynthSeg.

ANTs (resampling, N4, mask multiply) falls back to a local install
(`ResampleImage`, `N4BiasFieldCorrection`, `ImageMath` on `PATH`) if Docker
isn't available — there's no equivalent precomputed-file option for those.

**Optional arguments:**

* `--threads` (default `5`): threads for SynthSeg.
* `--laplacian_threshold` (default `0.21`)
* `--frangi_threshold` (default `0.25`)
* `--lower_frangi_threshold` (default `0.2`): used if the higher threshold finds no candidates.
* `--expand_radius` (default `6`): dilation radius applied to the final line mask.
* `--save_intermediate`: also save the thresholded Laplacian, Frangi, and combined masks.

## Citation

If you use this in your work, please cite the paper above — see [`CITATION.cff`](CITATION.cff)
for the full machine-readable record.

## Releasing

Publishing a GitHub Release triggers `.github/workflows/release.yml`, which
builds the package and publishes it to PyPI via
[trusted publishing](https://docs.pypi.org/trusted-publishers/) (no API token
stored in the repo). One-time setup on PyPI, before the first release:
add a trusted publisher on the `saline-dbs` project (or as a pending
publisher if the project doesn't exist yet) pointing at this repository,
workflow `release.yml`, environment `pypi`.
