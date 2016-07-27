#!/usr/bin/env python
import os
from abkhazia2abx import alignment2item
from abkhazia.corpus import Corpus

data_dir = '/home/mbernard/dev/abkhazia/egs/align_childes_brent'
corpus = Corpus.load(os.path.join(data_dir, 'data'))
alignment = os.path.join(data_dir, 'align', 'alignment2.txt')
items = os.path.join(data_dir, 'items.txt')

alignment2item(corpus, alignment, items, njobs=4, verbose=11)
