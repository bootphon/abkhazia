#!/usr/bin/env python
import os
from abkhazia2abx import alignment2item
from abkhazia.corpus import Corpus

corpus_dir = '/home/mathieu/lscp/dev/abkhazia/egs/align_childes_brent'
data_dir = os.path.dirname(__file__)
corpus = Corpus.load(os.path.join(data_dir, 'data'))
alignment = os.path.join(data_dir, 'align', 'alignment2.txt')
items = os.path.join(data_dir, 'items.txt')

alignment2item(corpus, alignment, items, njobs=4, verbose=11)
