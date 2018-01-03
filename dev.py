#!/usr/bin/env python

from abkhazia.corpus.prepare.kcss_preparator import KCSSPreparator
from abkhazia.utils.logger import get_log

kcss = KCSSPreparator(
    '/home/mathieu/lscp/data/KCSS', log=get_log(verbose=True))
kcss.copy_wavs = False

corpus = kcss.prepare('/home/mathieu/lscp/data/abkhazia/KCSS/wavs')
