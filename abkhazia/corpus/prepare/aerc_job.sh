#!/bin/bash
#SBATCH --job-name=aesrc             # Job name
#SBATCH --partition=all              # Take a node from the 'cpu' partition
#SBATCH --output=%x-%j.log            # Standard output and error log

echo "Running job on $hostname"#?

# load conda environment
source /shared/apps/anaconda3/envs/abkhazia
conda activate abkhazia

# launch your computation
python aesrc_dev.py # input_path output_path
