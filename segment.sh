#!/bin/bash
#SBATCH --job-name=segmentation
#SBATCH --output=logs/%x_%j.out
#SBATCH --time=0-12:00:00
#SBATCH --cpus-per-task=32
#SBATCH --mem 32GB
#SBATCH --gres=gpu:1
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=dario.bernasconi@unibe.ch

#### Config ####

# src_dir: Directories with images to segment.
# filter_out: Expression(s) to filter out specific files.
# channel: Which channel to segment.
# redo_seg: Whether to redo the segmentation if a mask already exists.
# batch_size: Number of tiles processed in parallel (decrease if you get out-of-memory errors).
# cellprob_treshold: Pixels are segmented if their probability of being part of an object is bigger than this.
# stitch_threshold: Masks in adjacent planes are stitched in 3D if the overlap is bigger than this. 
# min_size: Minimum object size in pixel. Smaller segmentations are discarded.
# max_size_fraction: Maximum obect size as a fraction of the image size. Bigger objects are discarded.
# cpsam_model: Name of the CPSAM (or path to a custom) model to use.
# mask_suffix: Suffix and file extension of the mask. File extension should be .tif, .npy or .npz.
# plot_range: Percentiles defining the data range for the QC plots.
# pixi_dir: Directory of the pixi workspace

src_dirs=(
 /Volumes/meister.data/dario/imaging/DPY27/test_max
# /Volumes/meister.data/dario/imaging/DPY27/test_1268
# /Volumes/meister.data/dario/imaging/DPY27/test_1268_dw
# /Volumes/meister.data/dario/imaging/DPY27/test_1268_l1_dw
# /Volumes/meister.data/dario/imaging/DPY27/1268/20260720_e/dw
# /Volumes/meister.data/dario/imaging/DPY27/1373/20260720_e/dw
# /Volumes/meister.data/dario/imaging/DPY27/1431/20260720_e/dw
)
filter_out=()
channel=0
redo_seg=true
batch_size=64
cellprob_threshold=0
stitch_threshold=0.5
min_size=15
max_size_fraction=0.1
cpsam_model=cpsam_v2
mask_suffix='mask.tif'
plot_range=(1 99.9)
pixi_dir=/Volumes/meister.data/dario/code/cpsam

#### Script ####

pixi_dir=${pixi_dir/Volumes/mnt}
cd $pixi_dir

for dir in ${src_dirs[@]}; do
    pixi run python segment.py \
    --src_dir ${dir/Volumes/mnt} \
    --filter_out ${filter_out[@]} \
    --channel $channel \
    --redo_seg $redo_seg \
    --batch_size $batch_size \
    --cellprob_threshold $cellprob_threshold \
    --stitch_threshold $stitch_threshold \
    --min_size $min_size \
    --max_size_fraction $max_size_fraction \
    --cpsam_model $cpsam_model \
    --mask_suffix $mask_suffix \
    --plot_range ${plot_range[@]}
done
