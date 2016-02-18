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
import subprocess

#root = '/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia'
#kaldi_root = '/Users/thomas/Documents/PhD/Recherche/kaldi/kaldi-trunk'
root = '/fhgfs/bootphon/scratch/thomas/abkhazia'
kaldi_root = '/fhgfs/bootphon/scratch/thomas/kaldi'

corpora = ['Buckeye']  #['GP_Mandarin', 'GP_Vietnamese']
prune_lexicons = [True]  #[False, True]

for corpus, prune_lexicon in zip(corpora, prune_lexicons):
    # Instantiate forced alignment recipe
    force_align.create_kaldi_recipe(
        p.join(root, 'corpora', corpus),
        p.join(root, 'kaldi', corpus),
        kaldi_root)

    # Instantiate posterior decoding recipe. Cutting corpus in half
    # and using different speakers for train and test sets
    split.train_test_split(
        p.join(root, 'corpora', corpus),
        train_proportion=.5,
        split_speakers=False)

    decode.create_kaldi_recipe(
        p.join(root, 'corpora', corpus),
        p.join(root, 'kaldi', corpus),
        kaldi_root,
        prune_lexicon=prune_lexicon)

    ## Run the recipes
    # how to set the parameters here easily?
    # subprocess.call(cd recipe_path; ./run.sh)

    ## Check and process the results
    # include an ad hoc part relying on undocumented kaldi features

    # add an alignments folder to data
    # add a features folder to data ??? (probably somewhere else?)

# """
# # test on Buckeye for challenge
# corpus_path = '/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/corpora/Buckeye'
# all_speakers = [
# 				u's08', u's09', u's01', u's02',
# 				u's03', u's04', u's05', u's06',
# 				u's07', u's36', u's35', u's34',
# 				u's40', u's37', u's31', u's19',
# 				u's18', u's39', u's38', u's13',
# 				u's12', u's11', u's10', u's17',
# 				u's16', u's15', u's14', u's33',
# 				u's32', u's30', u's22', u's23',
# 				u's20', u's21', u's26', u's27',
# 				u's24', u's25', u's28', u's29'
# 			]
# test_speakers = [
# 			u's01', u's20', u's23', u's24',
# 			u's25', u's26', u's27', u's29',
# 			u's30', u's31', u's32', u's33'
# 			]
# train_speakers = list(set.difference(set(all_speakers), set(test_speakers)))
# train_test_split(corpus_path, train_speakers=train_speakers, split_speakers=False)
# """

# # test on NCHLT_Tsonga for challenge
# """
# corpus_path = '/fhgfs/bootphon/scratch/thomas/abkhazia/corpora/NCHLT_Tsonga'
# all_speakers = [
# 			u'149f', u'021m', u'084m', u'131f',
# 			u'109f', u'506f', u'179m', u'130m',
# 			u'103f', u'012m', u'115f', u'004f',
# 			u'122f', u'166m', u'141m', u'033f',
# 			u'060m', u'092m', u'106m', u'053f',
# 			u'182f', u'072m', u'043f', u'083f',
# 			u'167m', u'177m', u'507f', u'502f',
# 			u'172f', u'013m', u'003f', u'023f',
# 			u'178f', u'114m', u'063f', u'030m',
# 			u'146f', u'014m', u'093m', u'054f',
# 			u'042f', u'073m', u'183m', u'086m',
# 			u'135m', u'505m', u'090m', u'046f',
# 			u'126f', u'010m', u'026f', u'154m',
# 			u'113m', u'123m', u'133f', u'500m',
# 			u'148f', u'098m', u'153f', u'045m',
# 			u'074m', u'059m', u'019f', u'066f',
# 			u'164f', u'029m', u'035f', u'051f',
# 			u'143m', u'184f', u'156f', u'151m',
# 			u'085f', u'138m', u'069m', u'107f',
# 			u'011f', u'134m', u'104f', u'108m',
# 			u'005f', u'112f', u'132m', u'061m',
# 			u'101m', u'150m', u'075m', u'044f',
# 			u'020m', u'165f', u'140f', u'099m',
# 			u'032f', u'052f', u'091m', u'028f',
# 			u'118m', u'173f', u'171m', u'159m',
# 			u'152m', u'186m', u'096m', u'024f',
# 			u'016m', u'116m', u'048f', u'121m',
# 			u'076m', u'174m', u'120f', u'088m',
# 			u'057f', u'110m', u'007m', u'501m',
# 			u'037m', u'162f', u'047m', u'080f',
# 			u'064m', u'145m', u'155m', u'187f',
# 			u'190m', u'087m', u'170f', u'097m',
# 			u'027f', u'503m', u'017m', u'175f',
# 			u'068f', u'006m', u'058m', u'067f',
# 			u'077m', u'018f', u'034f', u'163f',
# 			u'139f', u'102f', u'142m', u'144m',
# 			u'050f', u'158f', u'188m', u'125m',
# 			u'504f', u'078m', u'094f', u'038f',
# 			u'022m', u'117m', u'127f', u'002m',
# 			u'136f', u'009m', u'157m', u'055m',
# 			u'062m', u'031f', u'015m', u'176f',
# 			u'070f', u'147m', u'180f', u'161m',
# 			u'041f', u'128m', u'082f', u'160f',
# 			u'137m', u'095m', u'079f', u'189f',
# 			u'100m', u'039m', u'001m', u'025f',
# 			u'049f', u'169f', u'008m', u'111f',
# 			u'056f', u'089m', u'168f', u'129f',
# 			u'071f', u'081m', u'124m', u'185f',
# 			u'040f', u'065f', u'181m', u'119f',
# 			u'105m', u'036f'
# 			]

# test_speakers = [
# 			u'130m', u'139f', u'132m', u'102f',
# 			u'128m', u'103f', u'146f', u'134m',
# 			u'104f', u'135m', u'141m', u'001m',
# 			u'142m', u'131f', u'126f', u'143m',
# 			u'138m', u'127f', u'144m', u'133f',
# 			u'145m', u'129f', u'140f', u'136f'
# 			]
# train_speakers = list(set.difference(set(all_speakers), set(test_speakers)))
# train_test_split(corpus_path, train_speakers=train_speakers, split_speakers=False)
# """
