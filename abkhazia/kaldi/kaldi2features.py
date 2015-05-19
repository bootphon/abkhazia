# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz


Exporting transcriptions and lattice posteriors from a kaldi recipe to h5features format. 
"""

import h5features
import numpy as np
import codecs
import os
import re
import abkhazia.kaldi.kaldi2abkhazia as k2a

# 1-best aligned transcription to h5features
def transcription2features():
	pass



# kaldi lattice posteriors to h5features
# this loads everything into memory, but it would be easy to write
# an incremental version if this poses a problem
def lattice2features(phones_file, post_file, out_file, word_position_dependent=True):
	phonemap = k2a.read_kaldi_phonemap(phones_file, word_position_dependent)
	# remove disambiguation symbols and <eps> from the phonemap,
	# as those shouldn't be in the posteriorgram
	codes = phonemap.keys()
	for code in codes:
		if re.match(u'#[0-9]+$|<eps>$', phonemap[code]):
			del phonemap[code]
	# get the order in which the phone will mapped over the 
	# dimensions of a posterior vector
	phone_order = list(np.unique(phonemap.values()))
	d = len(phone_order)  # posteriorgram dimension

	# below is basically a parser for kaldi matrix format for each line
	# parse input text file (this is too slow already...)
	with codecs.open(post_file, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()  # xreadlines supposed to be more efficient for large files	
	# here would be nice to use sparse feature format (need to have it in h5features though)
	# might want to begin by using sparse numpy matrix format
	features = []
	for index, line in enumerate(lines):
		print("Processing line {0} / {1}".format(index, len(lines)))
		tokens = line.strip().split(u" ")
		utt_id, tokens = tokens[0], tokens[1:]
		frames = []
		inside = False
		for token in tokens:
			if token == u"[":
				assert not(inside)
				inside = True
				frame = []
			elif token == u"]":
				assert inside
				inside = False
				frames.append(frame)
			else:
				assert inside
				frame.append(token)
		utt_features = np.zeros(shape=(d, len(frames)), dtype=np.float64)
		for f, frame in enumerate(frames):
			assert len(frame) % 2 == 0 
			probas = [float(p) for p in frame[1::2]]
			phones = [phonemap[code] for code in frame[::2]]
			# optimisation 1 would be mapping directly a given code to a given posterior dim
			for phone, proba in zip(phones, probas):
				i = phone_order.index(phone)
				# add to previous proba since different variants of a same phone will map to 
				# the same dimension i of the posteriorgram
				utt_features[i, f] = utt_features[i, f] + proba
		# normalize posteriorgrams to correct for rounding or thresholding errors
		# by rescaling globally
		total_proba = np.sum(utt_features, axis=0)
		if np.max(np.abs(total_proba-1)) >= 1e-6:  # ad hoc numerical tolerance...
			raise IOError("In utterance {0}, frame {1}: posteriorgram does not sum to one".format(utt_id, f))
		utt_features = utt_features/np.tile(total_proba, (d,1))
		features.append(utt_features)
	return phone_order, features
		
#TODO check posterior sum to one

# need to do a unique of the phone dims and remove <eps> from the phonemap
# posterior do not sum to one ... ???
# impact of acoustic_scale param ???

root = "/Users/Thomas/Documents/PhD/Recherche/test"
phones_file = os.path.join(root, 'phones_CSJ.txt')
post_file = os.path.join(root, 'post.post')
out_file = ""
phone_order, features = lattice2features(phones_file, post_file, out_file)


