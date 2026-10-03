# SALINE
### Segmentation Algorithm using LINe-fitting for Electrodes

*V. H. Yu et al., "DBS-ElecNet: Automated Localization and Segmentation of DBS Electrodes in Clinical MRI," 2026 IEEE 23rd International Symposium on Biomedical Imaging (ISBI), London, United Kingdom, 2026, pp. 1-4, doi:[10.1109/ISBI61048.2026.11515562](https://doi.org/10.1109/ISBI61048.2026.11515562)*

SALINE combines a Laplacian edge filter and a Frangi vesselness filter to find
electrode-track candidate voxels, then fits a line through them per electrode.
It runs as a standalone CLI tool; [DBS-ElecNet](https://github.com/srikash/DBS-ElecNet)
depends on it for its classical (non-deep-learning) segmentation pipeline.

## Why SALINE?

Expert-annotated DBS electrode segmentations are scarce and expensive. Manual
segmentation takes 3-5 minutes per scan, and there's basically no specialized
DBS MRI dataset with ground truth to start from. SALINE sidesteps that: it
segments a scan in about 1.5 minutes with no manual input, so you can run it
over an entire cohort instead of hand-labeling a few dozen scans.

That's literally how it was used in the DBS-ElecNet paper. SALINE ran over
280 post-operative MRI scans, and 258 of the resulting masks (211 train, 7
validation, 40 test) became DBS-ElecNet's training data, no manual annotation
anywhere in the pipeline. DBS-ElecNet ends up beating SALINE on exactly the
cases where the filter-based approach struggles: low-contrast regions near
the ventricles, bilateral electrodes that are hard to separate depending on
head orientation. Those are roughly the 22 scans that got excluded from
training. SALINE's job is to bootstrap the training set, not to nail every
scan on its own.

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
