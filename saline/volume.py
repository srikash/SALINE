import nibabel as nib


def get_shape(path):
    """Return the (dim1, dim2, dim3) voxel shape of a NIfTI volume at `path`."""
    return nib.load(path).get_fdata().shape
