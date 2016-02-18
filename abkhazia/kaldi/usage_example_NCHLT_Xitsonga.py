# -*- coding: utf-8 -*-
# Copyright 2015, 2016 Thomas Schatz
#
# This file is part of abkhazia: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Abkhazia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz


Getting forced alignments and posterior decoding on some corpora
"""

import abkhazia.utils.kaldi.train_test_split as split
import abkhazia.utils.kaldi.force_align as force_align
import abkhazia.utils.kaldi.train_and_decode as decode
import os.path as p
#import subprocess


root = '/home/mbernard/dev/abkhazia'
kaldi_root = '/home/mbernard/dev/kaldi'

corpora = ['NCHLT_Xitsonga']
prune_lexicons = [False]
for corpus, prune_lexicon in zip(corpora, prune_lexicons):
    # Instantiate forced alignment recipe
    force_align.create_kaldi_recipe(
        p.join(root, 'corpora', corpus),
        p.join(root, 'kaldi', corpus),
        kaldi_root)

    # Instantiate posterior decoding recipe. Cutting corpus in half
    # and using different speakers for train and test
    split.train_test_split(
        p.join(root, 'corpora', corpus),
        train_proportion=.9,
        split_speakers=False)

    decode.create_kaldi_recipe(
        p.join(root, 'corpora', corpus),
        p.join(root, 'kaldi', corpus),
        kaldi_root,
        prune_lexicon=prune_lexicon)

    ## Estimate LM for posterior decoding recipe from some text ???
    # or use LM in arpa-MIT format
    # or what?

    ## Run the recipes
    # how to set the parameters here easily?
    # subprocess.call(cd recipe_path; ./run.sh)

    ## Check and process the results
    # add an alignments folder to data
    # add a features folder to data ??? (probably somewhere else?)
