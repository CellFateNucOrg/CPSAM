# CPSAM
Segmentation of C. elegans microscopy images with Cellpose-SAM.
# Installation
Installation instructions are given for pixi, but you can also use conda/mamba.
1. If you don't have pixi yet, install it from:`https://pixi.prefix.dev/latest/installation/`
2. Navigate to where you want to place the repository.
3. Clone the repository: `git clone https://github.com/CellFateNucOrg/CPSAM/`
4. Install the required packages: `pixi install`
5. Confirm that CUDA is available (so you can run the pipeline with GPU support):
```
srun --gres gpu:1 --pty bash
pixi run python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
```
This should print something like:
```
2.14.0+cu130
13.0
True # This confirms that is CUDA available
```
# Use
Before you run the pipeline, open `segment.sh` and specify the parameters below. An important note retarding 3D images: 3D segmentation of signals that follow edges rather than filling out an entire nucleus or cell (such as EMR-1::mCherry) does not work well. For that reason, this pipeline uses so-called 2.5D segmentation: segmentation in 2D, followed by vertical stitching of adjacent masks based on a set threshold (see `stitch_threshold`).

* `src_dir=()`: List of one or more directories (separated by space or line) with images you want to segment.
* `filter_out=()`: Expression(s) (separated by space or line) to filter out specific files. If your input directory contains files you don't want to segment, use this option to filter them out.
* `channel`: Which channel you want to segment.
* `redo_seg`: Whether to override existing masks (`true` or `false`).
* `batch_size`: Number of tiles processes in parallel. Default is 64. Decrease if you get out-of-memory errors.
* `cellprob_threshold`: Threshold for deciding whether a pixel belongs to a mask. -6 to +6; default is 0. Decrease if your images are under-segmented and vice versa.
* `stitch_threshold`: Threshold for 3D stitching. Masks in adjacent planes which overlap by more than this value are stitched together, i.e., become part of the same 3D mask. 0 to 1; default is 0. Decrease this if you think your images are under-segmented in 3D and vice versa.
* `min_size`: Minimum mask size in pixels. Smaller segmentations are discarded. Default is 15.
* `max_size`: Maximum mask size as a fraction of total image size. Default is 0.4.
* `cpsam_model`: Name of the CPSAM model to use or a path to a custom-trained model. Default is `cpsam_v2`.
* `mask_str`: Suffix that differentiates the mask from its corresponding image (e.g., _mask.tif).
* `plot_range=()`: Percentiles defining what data range is used for the QC plots. Especially with deconvolved images, using the full data range leads to oversaturated plots. What works better (and should still be acceptable for raw images) is `(1, 0.99)`.
* `pixi_dir`: Path to this repository (including the folder `CPSAM` itself).

