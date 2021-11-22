#!/usr/bin/env python

import tempfile
from abkhazia.corpus import Corpus
from abkhazia.corpus.prepare import AESRCPreparator
from abkhazia.utils.logger import get_log

# define a logger with detailed messages
log = get_log(verbose=True)

# create the Buckeye Preparator
preparator = AESRCPreparator(
   '/home/mkhentout/Bureau/Dataset/abkhazia/American English Speech Data',
   #'/scratch1/data/raw_data/AESRC/Datatang-English/data/American English Speech Data'

    copy_wavs=False,log=log)
#/home/mkhentout/Bureau/Dataset/Datatang-English/data/American English Speech Data
# prepare the Buckeye corpus into abkhazia format (using a temp directory to
# store symlinks to the wavs)
with tempfile.TemporaryDirectory() as tmpdir:
    corpus = preparator.prepare(tmpdir)
    corpus.save('/home/mkhentout/Bureau/Dataset/abkhazia/tmp_American English Speech')
# load the prepared corpus and validate the format is correct
    corpus.validate()
