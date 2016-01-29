#!/usr/bin/env python
"""Convert the Xitsonga corpus to the abkhazia format"""

import sys
from abkhazia.corpora.utils import main
from abkhazia.corpora.xitsonga import XitsongaPreparator


# Raw distribution of the revised Buckeye corpus is available at:
# http://buckeyecorpus.osu.edu/ (TODO change link later when the
# revised version will be distributed)
INPUT_DIR = "/home/mbernard/data/nchlt_Xitsonga"

# Path to a directory where the processed corpora is to be stored
# output_dir = "/home/xcao/github_abkhazia/abkhazia/corpora/Buckeye/"
OUTPUT_DIR = "/home/mbernard/dev/abkhazia/corpora/NCHLT_Xitsonga/"


main(XitsongaPreparator, sys.argv + ' '.join([INPUT_DIR, OUTPUT_DIR]))
