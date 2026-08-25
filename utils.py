from pathlib import Path
from bioio import BioImage
from bioio_ome_tiff.writers import OmeTiffWriter
from datetime import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
from skimage.color import label2rgb
from skimage.segmentation import find_boundaries


__all__ = [
    'parse_path',
    'collect_images',
    'split_stack',
    'save_metadata',
    'plot_masks'
]


def parse_path(path, server=True):
    """
    Return a Path object and replaces 'Volumes' with 'mnt' if server is True.
    """
    if server:
        return Path(str(path).replace('Volumes', 'mnt'))
    else:
        return Path(path)


def collect_images(src_dir, ftypes=['.tif','.nd2','.czi','.lif'], filter_in=[], filter_out=[]):
    imgs = []
    for item in Path(src_dir).iterdir():
        if item.suffix not in ftypes:
            continue
        if not all(f in item.name for f in filter_in):
            continue
        if any(f in item.name for f in filter_out):
            continue
        imgs.append(item)
    return imgs


def split_stack(imgs, planes, output_dir, channel=0):
    """
    Extract substacks or slices from one or more stacks.

    Args:
        imgs (list[str], list[Path]): List of image paths.
        planes (list[int] or range): Planes (ints) or substack (range) to extract.
        outputdir (str, Path): Where to store the extracted slices.
        channel (int): Channel to extract. Default 0.

    Returns:
        List with paths of the extracted slices.
    """

    out = []
    for img in imgs:
        # Extract substack if 'planes' is a range
        if isinstance(planes, range):
           suffix = f'{img.stem}_c{str(channel).zfill(3)}_z{planes[0]}-{planes[-1]-1}'
           path = Path(output_dir) / f'{suffix}.tif' 
           out.append(path)
           data = BioImage(img).get_image_data('TCZYX', C=channel, Z=planes)
           OmeTiffWriter.save(data, path)

        # Extract slices if 'planes' is a list of ints
        elif isinstance(planes, list) and all(isinstance(zi, int) for zi in planes):
            for z in planes:
                suffix = f'{img.stem}_c{str(channel).zfill(3)}_z{str(z).zfill(3)}'
                path = Path(output_dir) / f'{suffix}.tif'
                out.append(path)
                data = BioImage(img).get_image_data('TCZYX', C=channel, Z=z)
                OmeTiffWriter.save(data, path)

    return out


def save_metadata(img, model, path, **args):
    params = {
        'image': img.name,
        'model': model.pretrained_model,
        'parameters': args,
        'created': datetime.now().isoformat(timespec='seconds')
    }
    with open(path, 'w') as f:
        json.dump(params, f, indent=4)


def plot_masks(img, mask, slices=[0.3, 0.5, 0.7], pths=(0, 100), path=None, show=True):
    """
    Plot image slices overlaid with the contours of the corresponding masks.

    Args:
        img (str or Path): Image data with shape 'TCZYX'.
        mask (str or Path): Mask data with shape 'TCZYX'.
        slices (list[floats]): Decimals indicating which slices to plot in each dimension.
        pths (tuple[floats]): Percentiles defining the data range for the plots. Default (0, 100).
        path (str or Path): Path for saving the figure. Ignored if not set.
        show (bool): Whether to print the figure inline.
    """
    # Get dims
    z, y, x = BioImage(img).dims['Z', 'Y', 'X']
    min_value = np.percentile(img, min(pths))
    max_value = np.percentile(img, max(pths))

    # Make figure and subfigures
    fig = plt.figure(layout='constrained', dpi=450, figsize=(10, 10))

    # Make one subfigure each for x-y, x-z, and y-z
    subfigs = fig.subfigures(nrows=3, ncols=1)
    xy_fig = subfigs[0].subplots(nrows=1, ncols=3, sharex=True, sharey=True)
    xz_fig = subfigs[1].subplots(nrows=1, ncols=3, sharex=True, sharey=True)
    yz_fig = subfigs[2].subplots(nrows=1, ncols=3, sharex=True, sharey=True)

    # Plot 2D data in x-y
    if z == 1:
        # Label edges
        edges = find_boundaries(mask, mode='thick')
        contours = label2rgb(edges * mask, bg_label=0)

        # Plot image & cotours
        xy_fig[0].imshow(
            img[:, :],
            cmap='gray_r',
            vmin=min_value,
            vmax=max_value
        )
        xy_fig[0].imshow(contours, alpha=(edges != 0))
        xy_fig[0].set_title(f'Z=0', fontsize=8)

        # Remove spines from empty subplots
        for spine in ['top', 'right', 'bottom', 'left']:
            xy_fig[1].spines[spine].set_visible(False)
            xy_fig[2].spines[spine].set_visible(False)
            for i in range(3):
                xz_fig[i].spines[spine].set_visible(False)
                yz_fig[i].spines[spine].set_visible(False)

    # Plot 3D data x-y, x-z, and y-z
    else:
        print(mask.shape)
        for i, s in enumerate(slices):
            # Get slices
            zi = min(int(z * s), z - 1)            
            yi = min(int(y * s), y - 1)
            xi = min(int(x * s), x - 1)

            # Label edges
            edges_z = find_boundaries(mask[zi, :, :], mode='thick')
            contours_z = label2rgb(edges_z * mask[zi, :, :], bg_label=0)
            edges_y = find_boundaries(mask[:, yi, :], mode='thick')
            contours_y = label2rgb(edges_y * mask[:, yi, :], bg_label=0)
            edges_x = find_boundaries(mask[:, :, xi], mode='thick')
            contours_x = label2rgb(edges_x * mask[:, :, xi], bg_label=0)

            # Plot image & contours in x-y
            xy_fig[i].imshow(
                img[zi, :, :],
                cmap='gray_r',
                vmin=min_value,
                vmax=max_value
            )
            xy_fig[i].imshow(contours_z, alpha=(edges_z != 0))
            xy_fig[i].set_title(f'Z={zi}', fontsize=8)

            # Plot image & contours in x-z
            xz_fig[i].imshow(
                img[:, yi, :],
                cmap='gray_r',
                vmin=min_value,
                vmax=max_value
            )
            xz_fig[i].imshow(contours_y, alpha=(edges_y != 0))
            xz_fig[i].set_title(f'Y={yi}', fontsize=8)

            # Plot image & contours in y-z
            yz_fig[i].imshow(
                img[:, :, xi],
                cmap='gray_r',
                vmin=min_value,
                vmax=max_value
                )
            yz_fig[i].imshow(contours_x, alpha=(edges_x != 0))
            yz_fig[i].set_title(f'X={xi}', fontsize=8)

    # Remove ticks
    for subfig in zip(xy_fig, xz_fig, yz_fig):
        for plot in subfig:
            plot.set_xticks([])
            plot.set_yticks([])

    # Show and/or save the figure
    if show:
        plt.show()
    if path is not None:
        fig.savefig(path)
        plt.close()