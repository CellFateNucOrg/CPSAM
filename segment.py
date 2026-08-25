import argparse
from pathlib import Path
from bioio import BioImage
from bioio_ome_tiff.writers import OmeTiffWriter
import numpy as np
from cellpose import models
import polars as pl
from utils import *


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src_dir', required=True, help='Folder with images to segment.')
    parser.add_argument('--filter_out', required=True, nargs='*', help='Expression(s) to filter out files from the segmentation.')
    parser.add_argument('--redo_seg', required=True, help='Whether to redo the segmentation if a mask already exists')
    parser.add_argument('--seg_channel', required=True, type=int, help='Which channel to segment.')
    parser.add_argument('--batch_size', required=True, type=int, help='Number of tiles processed in parallel.')
    parser.add_argument('--cellprob_threshold', required=True, type=float, help='Pixels are segmented if their probability of being part of an object is bigger than this.')
    parser.add_argument('--stitch_threshold', required=True, type=float, help='Masks in adjacent planes are stitched in 3D if the overlap is bigger than this.')
    parser.add_argument('--min_size', required=True, type=int, help='Minimum object size in pixel. Smaller segmentations are discarded.')
    parser.add_argument('--max_size_fraction', type=float, required=True, help='Maximum object size as a fraction of image size. Bigger segmentations are discarded.')
    parser.add_argument('--cpsam_model', required=True, help='Name of the CPSAM (or path to a custom) model to use.')
    parser.add_argument('--mask_type', required=True, help='Suffix and file extension of the mask. File extension should be .tif, .npy or .npz')
    parser.add_argument('--plot_range', required=True, nargs=2, help='Percentiles defining the data range for the QC plots.')
    return parser.parse_args()


def main():
    args = get_args()
    src_dir = Path(args.src_dir)
    filter_out = [f for f in args.filter_out]
    redo_seg = args.redo_seg.lower() in ('1', 'true', 'yes')
    seg_channel = args.seg_channel
    batch_size = args.batch_size
    cellprob_threshold = args.cellprob_threshold
    stitch_threshold = args.stitch_threshold
    min_size = args.min_size
    max_size_fraction = args.max_size_fraction
    cpsam_model = args.cpsam_model
    mask_type = args.mask_type
    pths = tuple(float(f) for f in args.plot_range)
    
    # Collect images
    seg_imgs = collect_images(parse_path(src_dir), filter_out=filter_out)

    # Load model
    load_model = models.CellposeModel(pretrained_model=cpsam_model, gpu=True)

    # Make dirs
    masks_dir = src_dir / 'masks'
    masks_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = masks_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Make list and path for QC
    qcs = []

    # Loop over images
    for img in seg_imgs:
        # Read image & get dims
        load_img = BioImage(img)
        t, z = load_img.dims['T', 'Z']

        # Set CPSAM parameters
        cpsam_params = {
            'batch_size': batch_size,
            'cellprob_threshold': cellprob_threshold,
            'min_size': min_size,
            'max_size_fraction': max_size_fraction,
            'z_axis': None
        }

        # Add stitch threshold & set Z axis if the data is 3D
        if z > 1:
            cpsam_params['z_axis'] = 0
            cpsam_params['stitch_threshold'] = stitch_threshold

        # Make path for mask
        mask_path = masks_dir / f'{img.stem}_{mask_type}'

        # Segment image if there's no mask or redo_seg is True
        if not mask_path.exists() or redo_seg:
            # Make list for the masks
            masks = []

            # Make path for log file
            metadata_path = logs_dir / f'{img.stem}.json'

            for ti in range(t):
                # Make path for plot
                plot_path = masks_dir / f'{img.stem}_t{ti:03}_plots.pdf'

                # Get data from time point
                data_t = load_img.get_image_data(
                    'TCZYX',
                    T=ti,
                    C=seg_channel
                ).squeeze()

                # Segment data
                mask, _, _ = load_model.eval(
                        data_t,
                        **cpsam_params
                )
                masks.append(mask)

                # Make QC plots
                plot_masks(
                    img=data_t,
                    mask=mask,
                    pths=pths,
                    path=plot_path,
                    show=False
                )

            # Stack & save masks
            masks = np.stack(masks)
            if mask_path.suffix == '.tif':
                OmeTiffWriter.save(masks, mask_path)
            elif mask_path.suffix == '.npy':
                np.save(mask_path, masks)
            elif mask_path.suffix == '.npz':
                np.savez(mask_path, masks)

            # Save log
            save_metadata(
                img=img,
                model=load_model,
                path=metadata_path,
                **cpsam_params
            )

        # Else load the existing mask
        else:
            load_mask = BioImage(mask_path)
            masks = load_mask.get_image_data('TCZYX')

        if z > 1:
            cpsam_params.pop('z_axis')
            cpsam_params.pop('stitch_threshold')

if __name__=='__main__':
    main()
