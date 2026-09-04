# CPSAM
Segmentation of C. elegans microscopy images with Cellpose-SAM.
# Installation
...
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

