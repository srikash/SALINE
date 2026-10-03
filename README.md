# SALINE
### Filter-based localization and segmentation of DBS electrodes in clinical MRI

SALINE combines a Laplacian edge filter and a Frangi vesselness filter to find
electrode-track candidate voxels, then fits a line through them per electrode.
It runs as a standalone CLI tool; [DBS-ElecNet](https://github.com/srikash/DBS-ElecNet)
depends on it for its classical (non-deep-learning) segmentation pipeline.

## Install

```bash
pip install git+https://github.com/srikash/SALINE.git@v0.1.0
```

## Usage

Dual-electrode (default):

```bash
saline --input subject.nii.gz --br_mask subject_brain_mask.nii.gz --synthseg subject_seg.nii.gz
```

Single-electrode:

```bash
saline single --input subject.nii.gz --br_mask subject_brain_mask.nii.gz --synthseg subject_seg.nii.gz
```

**Required arguments:**

* `--input`: path to the input MRI volume (NIfTI format), already resampled to
  1mm isotropic, skull-stripped, and N4 bias-corrected.
* `--br_mask`: path to the corresponding brain mask.
* `--synthseg`: path to the corresponding SynthSeg segmentation.

**Output:**

* `subject_saline_elec.nii.gz`: the electrode segmentation, in the same space as `--input`.

**Optional arguments:**

* `--laplacian_threshold` (default `0.21`)
* `--frangi_threshold` (default `0.25`)
* `--lower_frangi_threshold` (default `0.2`): used if the higher threshold finds no candidates.
* `--expand_radius` (default `6`): dilation radius applied to the final line mask.
* `--save_intermediate`: also save the thresholded Laplacian, Frangi, and combined masks.
