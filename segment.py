import argparse
from pathlib import Path
from bioio import BioImage
import numpy as np
from cellpose import models
import json
from datetime import datetime
from utils import parse_path, collect_images, save_mask
from qc import plot_masks


def relabel_dupes(mask):
    """
    Relabel duplicate labels between time points.
    """
    for ti in range(mask.shape[0]):
        data_t = mask[ti, ...]
        labels = np.unique(data_t[data_t > 0])
        if ti == 0:
            used_labels = set(labels.tolist())
        else:
            for label in labels:
                if label in used_labels:
                    next_label = max(used_labels) + 1
                    data_t[data_t == label] = next_label
                    used_labels.add(next_label)
                else:
                    used_labels.add(label)
    return mask


def track_cells():
    """
    WIP: Track cells across frames using btrack and update the labels accordingly.
    """
    import btrack
    tracker = btrack.BayesianTracker()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src_dir', required=True, help='Directories with images to segment.')
    parser.add_argument('--filter_out', required=True, nargs='*', help='Expression(s) to filter out specific files.')
    parser.add_argument('--skip_old', required=True, help='Whether to skip previously segmented images.')
    parser.add_argument('--channel', required=True, type=int, help='Which channel to segment.')
    parser.add_argument('--track_cells', required=True, help='Whether to track cell nuclei across time points and through cell divisions.')
    parser.add_argument('--batch_size', required=True, type=int, help='Number of tiles processed in parallel.')
    parser.add_argument('--cellprob_threshold', required=True, type=float, help='Pixels are segmented if their probability of being part of an object is bigger than this.')
    parser.add_argument('--stitch_threshold', required=True, type=float, help='Masks in adjacent planes are stitched in 3D if the overlap is bigger than this.')
    parser.add_argument('--min_size', required=True, type=int, help='Minimum object size in pixel. Smaller segmentations are discarded.')
    parser.add_argument('--max_size_fraction', type=float, required=True, help='Maximum object size as a fraction of image size. Bigger segmentations are discarded.')
    parser.add_argument('--cpsam_model', required=True, help='Name of the CPSAM (or path to a custom) model to use.')
    parser.add_argument('--mask_str', required=True, help='Suffix and file extension of the mask. File extension should be .tif, .npy or .npz')
    parser.add_argument('--plot_range', required=True, nargs=2, help='Percentiles defining the data range for the QC plots.')
    return parser.parse_args()


def main():
    args = get_args()
    src_dir = Path(args.src_dir)
    filter_out = [f for f in args.filter_out]
    skip_old = args.skip_old.lower() in ('1', 'true')
    channel = args.channel
    track_cells = args.track_cells.lower() in ('1', 'true')
    batch_size = args.batch_size
    cellprob_threshold = args.cellprob_threshold
    stitch_threshold = args.stitch_threshold
    min_size = args.min_size
    max_size_fraction = args.max_size_fraction
    cpsam_model = args.cpsam_model
    mask_str = args.mask_str
    pths = tuple(float(f) for f in args.plot_range)

    
    # Collect images
    imgs = collect_images(parse_path(src_dir), filter_out=filter_out)

    # Load model
    model = models.CellposeModel(pretrained_model=cpsam_model, gpu=True)

    # Make dirs
    masks_dir = src_dir / 'masks'
    masks_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = masks_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    qc_dir = masks_dir / 'qc'
    qc_dir.mkdir(parents=True, exist_ok=True)

    # Loop over images
    for img_path in imgs:
        # Make path for the mask
        mask_path = masks_dir / f'{img_path.stem}{mask_str}'

        # Segment image if a mask doesn't exist yet or skip_old is False
        if mask_path.exists() and skip_old:
            continue
        else:
            print(f'Segmenting image {img_path.name}')

            # Read image & get dims
            img = BioImage(img_path)
            t, z = img.dims['T', 'Z']

            # Set CPSAM parameters
            cpsam_params = {
                'batch_size': batch_size,
                'cellprob_threshold': cellprob_threshold,
                'min_size': min_size,
                'max_size_fraction': max_size_fraction,
            }

            # Set Z axis & add stitching threshold if the image is 3D
            if z > 1:
                cpsam_params['z_axis'] = 0
                cpsam_params['stitch_threshold'] = stitch_threshold
            
            # Make list for the masks
            t_masks = []

            # Segment each frame
            for ti in range(t):
                # Segment data from current time point
                data = img.get_image_data(
                    'TCZYX',
                    T=ti,
                    C=channel
                ).squeeze()
                mask_data, _, _ = model.eval(data, **cpsam_params)

                # If the mask contains a single frame, plot it and expand its dims for saving
                if t == 1:
                    qc_path = qc_dir / f'{img_path.stem}.pdf'
                    plot_masks(
                        img=data,
                        mask=mask_data,
                        pths=pths,
                        path=qc_path,
                        show=False
                    )
                    mask = np.expand_dims(mask_data, axis=(0, 1)) # Add T & C axes

                # Else add it to the list for stacking
                else:
                    t_masks.append(mask_data)

            # If the mask contains multiple frames...
            if t > 1:
                # ...stack the frames
                mask = np.stack(t_masks, axis=0)

                # ...either track the cells with btrack or relabel duplicates manually
                if track_cells:
                    continue
                else:
                    mask = relabel_dupes(mask)

                # ...make one QC plot each
                for ti in range(t):
                    qc_path = qc_dir / f'{img_path.stem}_t{ti:03}.pdf'
                    data_t = img.get_image_data(
                        'TCZYX',
                        T=ti,
                        C=channel
                    ).squeeze()
                    mask_data_t = mask[ti, ...]
                    plot_masks(
                        img=data_t,
                        mask=mask_data_t,
                        pths=pths,
                        path=qc_path,
                        show=False
                    )

                # ...and lastly expand the dims for saving
                mask = np.expand_dims(mask, axis=1) # Add C axis

            # Save mask
            save_mask(mask, mask_path)

            # Save metadata
            metadata_path = logs_dir / f'{img_path.stem}.json'
            params = {
                'image': img_path.name,
                'model': model.pretrained_model,
                'parameters': cpsam_params,
                'created': datetime.now().isoformat(timespec='seconds')
            }
            with open(metadata_path, 'w') as f:
                json.dump(params, f, indent=4)


if __name__=='__main__':
    main()
