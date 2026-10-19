#!/bin/bash
#SBATCH --job-name=segmentation
#SBATCH --output=logs/%x_%j.out
#SBATCH --time=0-12:00:00
#SBATCH --cpus-per-task=32
#SBATCH --mem 64GB
#SBATCH --gres=gpu:1

#### Config ####

src_dirs=(

)
filter_out=(max bf)
skip_old=false
channel=0
track_cells=false
batch_size=64
cellprob_threshold=0
stitch_threshold=0.5
min_size=15
max_size_fraction=0.1
cpsam_model=cpsam_v2
mask_str='_mask.tif'
plot_range=(1 99.9)
pixi_dir=/path/to/cpsam

#### Script ####

pixi_dir=${pixi_dir/Volumes/mnt}
cd $pixi_dir

for dir in ${src_dirs[@]}; do
    pixi run python segment.py \
    --src_dir ${dir/Volumes/mnt} \
    --filter_out ${filter_out[@]} \
    --skip_old $skip_old \
    --channel $channel \
    --track_cells $track_cells \
    --batch_size $batch_size \
    --cellprob_threshold $cellprob_threshold \
    --stitch_threshold $stitch_threshold \
    --min_size $min_size \
    --max_size_fraction $max_size_fraction \
    --cpsam_model $cpsam_model \
    --mask_str $mask_str \
    --plot_range ${plot_range[@]}
done
