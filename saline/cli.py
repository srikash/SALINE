import os

import click
import nibabel as nib
from rich.console import Console
from tqdm import tqdm

from . import external
from .pipeline import preprocess
from .segment import segment

console = Console()

CITATION = (
    'V. H. Yu et al., "DBS-ElecNet: Automated Localization and Segmentation of DBS '
    'Electrodes in Clinical MRI," 2026 IEEE 23rd International Symposium on Biomedical '
    'Imaging (ISBI), London, United Kingdom, 2026, pp. 1-4, '
    'doi:10.1109/ISBI61048.2026.11515562'
)
CITATION_NOTICE = f"If you use this in your work, please cite {CITATION}"


class DefaultGroup(click.Group):
    """A click.Group where an unrecognized/absent subcommand falls back to one
    named command, so `saline --input ...` still means `saline dual --input ...`
    without `dual`'s options leaking onto the group itself (which would make
    them required even when running `saline single ...`).

    Click's own option parsing for the group runs before `resolve_command` is
    ever reached, so the default has to be injected in `parse_args`, before
    Click tries (and fails) to interpret `--input` as a group-level option."""

    def __init__(self, *args, default_command=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_command = default_command

    def parse_args(self, ctx, args):
        if args and args[0] not in ('-h', '--help') and (
            args[0].startswith('-') or args[0] not in self.commands
        ):
            args = [self.default_command, *args]
        return super().parse_args(ctx, args)


def _common_options(f):
    f = click.option('--input', 'input_path', required=True, type=str,
                      help='path to the raw, native-space input MRI')(f)
    f = click.option('--brain_mask', 'brain_mask_override', type=str, default=None,
                      help='precomputed brain mask (1mm-isotropic space); skips Docker-based SynthStrip')(f)
    f = click.option('--synthseg', 'synthseg_override', type=str, default=None,
                      help='precomputed SynthSeg segmentation (1mm-isotropic space); skips Docker-based SynthSeg')(f)
    f = click.option('--threads', type=int, default=5, show_default=True,
                      help='threads for SynthSeg')(f)
    f = click.option('--laplacian_threshold', type=float, default=0.21, show_default=True, help='the threshold value for laplacian filtered image')(f)
    f = click.option('--frangi_threshold', type=float, default=0.25, show_default=True, help='the threshold value for frangi filtered image')(f)
    f = click.option('--lower_frangi_threshold', type=float, default=0.2, show_default=True, help='the threshold value for frangi filtered image if the higher one failed')(f)
    f = click.option('--expand_radius', type=int, default=6, show_default=True, help='the radius of the final dilation')(f)
    f = click.option('--save_intermediate', is_flag=True, help='save intermediate images (thresholded laplacian and frangi images; combined image) if specified')(f)
    return f


def _run(num_regions, input_path, brain_mask_override, synthseg_override, threads,
          laplacian_threshold, frangi_threshold, lower_frangi_threshold,
          expand_radius, save_intermediate):
    nname = os.path.basename(input_path).split('.nii')[0]
    console.print(f"[bold]SALINE[/bold] start — [cyan]{nname}[/cyan]")

    with tqdm(desc="SALINE", unit="stage", leave=False) as bar:
        def on_stage(message):
            bar.set_description(message)
            bar.update(1)

        try:
            paths = preprocess(
                input_path, brain_mask_override=brain_mask_override,
                synthseg_override=synthseg_override, threads=threads, on_stage=on_stage,
            )
        except external.ExternalToolError as e:
            console.print(f"[red]✗[/red] {e}")
            raise SystemExit(1)

        img = nib.load(paths["n4"])
        br_mask_data = nib.load(paths["brain_mask"]).get_fdata()
        seg_data = nib.load(paths["synthseg"]).get_fdata()

        result = segment(
            img.get_fdata(), br_mask_data, seg_data, num_regions,
            laplacian_threshold, frangi_threshold, lower_frangi_threshold,
            expand_radius=expand_radius,
            save_intermediate=lambda name, array: (
                nib.save(nib.Nifti1Image(array.astype('uint8'), img.affine, img.header),
                          f"{paths['base']}_{name}.nii.gz")
                if save_intermediate else None
            ),
            on_stage=on_stage,
        )

        for intermediate in ("stripped", "brain_mask", "n4", "synthseg"):
            try:
                os.remove(paths[intermediate])
            except FileNotFoundError:
                pass

        if result is None:
            console.print(f"[red]✗[/red] no candidates found for [cyan]{nname}[/cyan], skipping")
            console.print(f"\n[dim]{CITATION_NOTICE}[/dim]")
            return

        on_stage("Resampling result back to native space")
        iso_result_path = f"{paths['base']}_1mm_iso_saline_elecSeg.nii.gz"
        nib.save(nib.Nifti1Image(result, img.affine, img.header), iso_result_path)
        native_result_path = f"{paths['base']}_saline_elecSeg.nii.gz"
        external.resample_to_native(iso_result_path, native_result_path, paths["native_shape"])

    console.print(f"[green]✓ SALINE done[/green] — [cyan]{nname}[/cyan]")
    console.print(f"\n[dim]{CITATION_NOTICE}[/dim]")


@click.group(cls=DefaultGroup, default_command='dual', epilog=CITATION_NOTICE)
def cli():
    """Segmenting the electrode(s) with SALINE."""


@cli.command(epilog=CITATION_NOTICE)
@_common_options
def dual(input_path, brain_mask_override, synthseg_override, threads,
          laplacian_threshold, frangi_threshold, lower_frangi_threshold,
          expand_radius, save_intermediate):
    """Dual-electrode mode (left/right split). This is the default."""
    _run(2, input_path, brain_mask_override, synthseg_override, threads,
         laplacian_threshold, frangi_threshold, lower_frangi_threshold,
         expand_radius, save_intermediate)


@cli.command(epilog=CITATION_NOTICE)
@_common_options
def single(input_path, brain_mask_override, synthseg_override, threads,
            laplacian_threshold, frangi_threshold, lower_frangi_threshold,
            expand_radius, save_intermediate):
    """Single-electrode mode."""
    _run(1, input_path, brain_mask_override, synthseg_override, threads,
         laplacian_threshold, frangi_threshold, lower_frangi_threshold,
         expand_radius, save_intermediate)


def main():
    cli()


if __name__ == "__main__":
    main()
