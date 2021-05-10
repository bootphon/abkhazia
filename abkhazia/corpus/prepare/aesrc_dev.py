#!/usr/bin/env python

import tempfile
from abkhazia.corpus import Corpus
from abkhazia.corpus.prepare import AESRCPreparator
from abkhazia.utils.logger import get_log

# define a logger with detailed messages
log = get_log(verbose=True)

# create the Buckeye Preparator
preparator = AESRCPreparator(
    '/home/mkhentout/Bureau/Dataset/abkhazia',
    copy_wavs=False,log=log)

# prepare the Buckeye corpus into abkhazia format (using a temp directory to
# store symlinks to the wavs)
with tempfile.TemporaryDirectory() as tmpdir:
    corpus = preparator.prepare(tmpdir)
    corpus.save('/home/mkhentout/Bureau/Dataset/tmp')
# load the prepared corpus and validate the format is correct
    corpus.validate()