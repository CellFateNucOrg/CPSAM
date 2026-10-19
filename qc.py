from pathlib import Path
from bioio import BioImage
from bioio_ome_tiff.writers import OmeTiffWriter
import numpy as np


def parse_path(path, server=True):
    """
    Return a Path object and replaces 'Volumes' with 'mnt' if server is True.
    """
    if server:
        return Path(str(path).replace('Volumes', 'mnt'))
    else:
        return Path(path)


def collect_images(src_dir, ftypes=('.tif', '.nd2', '.czi', '.lif'), filter_in=(), filter_out=()):
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


def save_mask(mask, mask_path):
    """
    Save mask as .tif, .npy, or .npz.
    """
    if mask_path.suffix == '.tif':
        OmeTiffWriter.save(mask, mask_path)
    elif mask_path.suffix == '.npy':
        np.save(mask_path, mask)
    elif mask_path.suffix == '.npz':
        np.savez(mask_path, mask)
    else:
        raise ValueError(f'Unsupported mask format: {mask_path.suffix}. Use .tif, .npy, or .npz.')
