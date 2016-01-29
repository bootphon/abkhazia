#!/usr/bin/env python
"""Convert the Buckeye corpus to the abkhazia format"""

import sys
from abkhazia.corpora.utils import main
from abkhazia.corpora.buckeye import BuckeyePreparator


# Raw distribution of the revised Buckeye corpus is available at:
# http://buckeyecorpus.osu.edu/ (TODO change link later when the
# revised version will be distributed)
BUCKEYE_PATH = "/home/mbernard/data/BUCKEYE_revised_original_format/"

# Path to a directory where the processed corpora is to be stored
# output_dir = "/home/xcao/github_abkhazia/abkhazia/corpora/Buckeye/"
OUTPUT_DIR = "/home/mbernard/dev/abkhazia/corpora/Buckeye/"

main(BuckeyePreparator, sys.argv + ' '.join([BUCKEYE_PATH, OUTPUT_DIR]))
