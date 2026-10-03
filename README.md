# SALINE
### Filter-based localization and segmentation of DBS electrodes in clinical MRI

*V. H. Yu et al., "DBS-ElecNet: Automated Localization and Segmentation of DBS Electrodes in Clinical MRI," 2026 IEEE 23rd International Symposium on Biomedical Imaging (ISBI), London, United Kingdom, 2026, pp. 1-4, doi:[10.1109/ISBI61048.2026.11515562](https://doi.org/10.1109/ISBI61048.2026.11515562)*

SALINE combines a Laplacian edge filter and a Frangi vesselness filter to find
electrode-track candidate voxels, then fits a line through them per electrode.
It runs as a standalone CLI tool; [DBS-ElecNet](https://github.com/srikash/DBS-ElecNet)
depends on it for its classical (non-deep-learning) segmentation pipeline.

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
