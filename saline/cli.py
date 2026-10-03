import argparse

import nibabel as nib

from .segment import segment


def _build_common_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--input', type=str, required=True, help='path to the input data')
    common.add_argument('--br_mask', type=str, required=True, help='path to the corresponding brain mask')
    common.add_argument('--synthseg', type=str, required=True, help='path to the corresponding synthseg segmentation')
    common.add_argument('--laplacian_threshold', type=float, default=0.21, help='the threshold value for laplacian filtered image')
    common.add_argument('--frangi_threshold', type=float, default=0.25, help='the threshold value for frangi filtered image')
    common.add_argument('--lower_frangi_threshold', type=float, default=0.2, help='the threshold value for frangi filtered image if the higher one failed')
    common.add_argument('--expand_radius', type=int, default=6, help='the radius of the final dilation')
    common.add_argument('--save_intermediate', action='store_true', help='save intermediate images (thresholded laplacian and frangi images; combined image) if specified')
    return common


def _derive_output_paths(input_path):
    file_split = input_path.rindex('/')
    nname = input_path[file_split + 1:].split('_skull')[0]
    save_folder = input_path[:file_split]
    return nname, save_folder


def _run(opt, num_regions):
    nname, save_folder = _derive_output_paths(opt.input)

    img = nib.load(opt.input)
    br_mask = nib.load(opt.br_mask).get_fdata()
    seg_img = nib.load(opt.synthseg).get_fdata()
    print("SALINE start -", nname)

    def save_intermediate(name, array):
        if opt.save_intermediate:
            nifti = nib.Nifti1Image(array.astype('uint8'), img.affine, img.header)
            nib.save(nifti, f"{save_folder}/{nname}_{name}.nii.gz")

    result = segment(
        img.get_fdata(), br_mask, seg_img, num_regions,
        opt.laplacian_threshold, opt.frangi_threshold, opt.lower_frangi_threshold,
        save_intermediate=save_intermediate,
    )
    if result is None:
        return

    nifti = nib.Nifti1Image(result, img.affine, img.header)
    nib.save(nifti, f"{save_folder}/{nname}_saline_elec.nii.gz")
    print("SALINE done")


def main():
    common = _build_common_parser()

    parser = argparse.ArgumentParser(description="Segmenting the electrode(s) with SALINE", parents=[common])
    subparsers = parser.add_subparsers(dest='mode')
    subparsers.add_parser('single', parents=[common], help='single-electrode mode')

    opt = parser.parse_args()
    num_regions = 1 if opt.mode == 'single' else 2
    _run(opt, num_regions)


if __name__ == "__main__":
    main()
