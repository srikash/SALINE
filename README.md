# SALINE
### Segmentation Algorithm using LINe-fitting for Electrodes

*V. H. Yu et al., "DBS-ElecNet: Automated Localization and Segmentation of DBS Electrodes in Clinical MRI," 2026 IEEE 23rd International Symposium on Biomedical Imaging (ISBI), London, United Kingdom, 2026, pp. 1-4, doi:[10.1109/ISBI61048.2026.11515562](https://doi.org/10.1109/ISBI61048.2026.11515562)*

SALINE combines a Laplacian edge filter and a Frangi vesselness filter to find
electrode-track candidate voxels, then fits a line through them per electrode.
It runs as a standalone CLI tool; [DBS-ElecNet](https://github.com/srikash/DBS-ElecNet)
depends on it for its classical (non-deep-learning) segmentation pipeline.

## Why SALINE?

Expert-annotated DBS electrode segmentations are scarce and expensive: manual
segmentation took 3-5 minutes per scan, and specialized DBS MRI datasets with
ground truth are nearly unavailable. SALINE exists to remove that bottleneck —
it segments a scan in about 1.5 minutes, with no manual input, which makes it
practical to run over an entire cohort rather than a handful of hand-labeled
examples.

That's exactly how it was used in the DBS-ElecNet paper: SALINE was run over
280 post-operative MRI scans to generate electrode masks, 258 of which (211
train, 7 validation, 40 test) became the training data for DBS-ElecNet's 3D
U-Net — no manual annotation involved anywhere in the loop. DBS-ElecNet then
goes on to outperform SALINE itself, including on scans where SALINE's
filter-based approach struggles (e.g. low-contrast regions near the
ventricles, or separating bilateral electrodes under certain head
orientations) — 22 of the 280 scans were excluded from training for exactly
this reason. SALINE's role is to bootstrap that training set, not to be the
final word on any individual scan.

## Install

Requires Python 3.12+.

```bash
pip install git+https://github.com/srikash/SALINE.git@v0.2.1
```

## Usage

Dual-electrode (default — also available explicitly as `saline dual`):

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

## Citation

If you use this in your work, please cite the paper above — see [`CITATION.cff`](CITATION.cff)
for the full machine-readable record.
