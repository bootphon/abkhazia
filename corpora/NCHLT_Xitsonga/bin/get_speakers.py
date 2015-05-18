# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 01:23:57 2015

@author: Thomas Schatz
"""

import codecs

filename='/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/corpora/NCHLT_Tsonga/data/utt2spk.txt'
with codecs.open(filename, mode='r', encoding='UTF-8') as inp:
	lines = inp.readlines()
speakers = set()
for line in lines:
	speaker = line.strip().split(u" ")[1]
	speakers.add(speaker)