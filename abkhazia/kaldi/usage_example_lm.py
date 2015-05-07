# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz


Getting forced alignments and posterior decoding on some corpora
"""

import abkhazia.kaldi.phone_loop_lm as phone_loop
import os.path as p

#root = '/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia'
#kaldi_root = '/Users/thomas/Documents/PhD/Recherche/kaldi/kaldi-trunk'
root = '/fhgfs/bootphon/scratch/thomas/abkhazia'
kaldi_root = '/fhgfs/bootphon/scratch/thomas/kaldi'

corpora = ['GP_Mandarin', 'GP_Vietnamese', 'WSJ_main_read', 'CSJ_core_laymen']
for corpus in corpora:
	corpus_path = p.join(root, 'corpora', corpus)
	recipe_path = p.join(root, 'kaldi', corpus, 'train_and_decode', 's5')
	phone_loop.setup_phone_loop(corpus_path,\
    							   recipe_path,\
    							   name="phone_loop")