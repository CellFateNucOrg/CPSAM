#!/bin/bash
#SBATCH --job-name=segmentation
#SBATCH --output=logs/%x_%j.out
#SBATCH --time=0-12:00:00
#SBATCH --cpus-per-task=32
#SBATCH --mem 32GB
#SBATCH --gres=gpu:rtx6000:1

#### Config ####

# src_dir: Directories with images to segment.
# ftype: File extension of the input images.
# redo_seg: Whether to redo the segmentation (and overwrite exisiting masks)
# seg_channel: Which channel to segment.
# quant_channel: For which channel to do the measurements.
# batch_size: Number of tiles processed in parallel (decrease if you get out-of-memory errors).
# cellprob_treshold: Cutoff for pixels to be part of an object; decrease if your images are "under-segmented" and vice versa.
# min_size: Minimum object size in pixel; smaller objects are discarded.
# max_size_fraction: Maximum obect size as a fraction of the image size; bigger objects are discarded.
# cpsam_model: Name of the CPSAM model to use or path to a custom model.
# plot_range: Percentiles defining the data range for the QC plots.

src_dirs=(

)
filter_out=(max)
seg_channel=0
redo_seg=true
batch_size=64
cellprob_threshold=0
stitch_threshold=0.5
min_size=15
max_size_fraction=0.1
cpsam_model=cpsam_v2
mask_type='mask.tif'
plot_range=(1 99.9)
pixi_dir=

#### Script ####

pixi_dir=${pixi_dir/Volumes/mnt}
cd $pixi_dir

for dir in ${src_dirs[@]}; do
    dir=${dir/Volumes/mnt}
    pixi run python segment.py \
    --src_dir $dir \
    --filter_out ${filter_out[@]} \
    --seg_channel $seg_channel \
    --redo_seg $redo_seg \
    --batch_size $batch_size \
    --cellprob_threshold $cellprob_threshold \
    --stitch_threshold $stitch_threshold \
    --min_size $min_size \
    --max_size_fraction $max_size_fraction \
    --cpsam_model $cpsam_model \
    --mask_type $mask_type \
    --plot_range ${plot_range[@]}
done
