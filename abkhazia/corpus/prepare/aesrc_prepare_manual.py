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
    log=log,copy_wavs=False)

# prepare the Buckeye corpus into abkhazia format (using a temp directory to
# store symlinks to the wavs)
with tempfile.TemporaryDirectory() as tmpdir:
    corpus = preparator.prepare(tmpdir)
    # save the prepared corpus to disk
    corpus.save('AES/abkkazia_aesrc')

# load the prepared corpus and validate the format is correct
corpus = Corpus.load('/home/mkhentout/Bureau/Dataset/abkhazia/AESRC', log=log)
corpus.validate()