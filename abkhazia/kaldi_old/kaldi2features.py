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


Exporting transcriptions and lattice posteriors from a kaldi recipe to h5features format.
"""

import h5features
import numpy as np
import codecs
import os
import re
import abkhazia.kaldi.kaldi2abkhazia as k2a
import os.path as p


def get_phone_order(phonemap):
	"""
	Output an easily reproducible phone order from a phonemap
	obtained by reading a phones.txt file with k2a.read_kaldi_phonemap
	"""
	# remove kaldi disambiguation symbols and <eps> from the phonemap,
	# as those shouldn't be in the phone_order
	codes = phonemap.keys()
	for code in codes:
		if re.match(u'#[0-9]+$|<eps>$', phonemap[code]):
			del phonemap[code]
	# order the phones in an easily reproducible way
	# unique is needed since there can be several variants of each phone in the map
	phone_order = list(np.unique(phonemap.values()))
	phone_order.sort()  # to guarantee reproducible ordering
	return phone_order


def transcription2features(phones_file, tra_file, out_file, word_position_dependent=True):
	"""
	Kaldi 1-best aligned transcription to h5features
	format in h5features is frame by frame, as this allows
	both frame-to-frame DTW distance and edit distance to be used
	(for edit_distance the first step would be extracting the phone-level
	sequence from the frame-level sequence, discarding segments that have
	too few frames)

	This avoids problems with long phones if coding only the centerpoint
	of a phone (a long time interval within the phone, but that does not
	include the centerpoint will have empty representation). Allowing
	representations indexed by time intervals instead of time points could
	be more elegant when one wants to use edit_distance but this would require
	some (substantial but not huge) recoding in h5features and ABXpy.distances.
	One would need to check that the time-intervals have no overlap and are
	consecutive and one would need to adapt the features reading to provide the
	sequence of consecutive feature vectors with their durations and for the first
	and last their degree of overlap with the required time segment.
	"""
	phonemap = k2a.read_kaldi_phonemap(phones_file, word_position_dependent)
	# get order used to encode the phones as integer in the features files
	phone_order = get_phone_order(phonemap)
	utt_ids = []
	times = []
	features = []
	current_utt = None
	utt_times = []
	utt_features = []
	i = 1
	for utt_id, start, stop, phone in k2a.read_kaldi_alignment(phonemap, tra_file):
		print i
		i = i+1
		if current_utt is None:
			current_utt = utt_id
		if utt_id != current_utt:
			utt_ids.append(current_utt)
			times.append(np.array(utt_times))
			nb_phones = len(utt_features)
			# not sure how h5features handles 1-d arrays, so reshaping
			features.append(np.array(utt_features).reshape((nb_phones, 1)))
			current_utt = utt_id
			utt_times = []
			utt_features = []
		else:
			# expanding to frame by frame using ad hoc 10ms window spacing
			# since start and stop are spaced by a multiple of 10ms due to
			# standard window spacing used by kaldi
			nframes = (stop-start)/0.01
			assert np.abs(nframes-np.round(nframes)) < 1e-7  # ad hoc tolerance
			nframes = int(np.round(nframes))
			utt_features = utt_features + [phone_order.index(phone)]*nframes
			frame_times = start + 0.01*np.arange(nframes)
			utt_times = utt_times + list(frame_times)
	h5features.write(out_file, 'features', utt_ids, times, features)


def lattice2features(phones_file, post_file, out_file, word_position_dependent=True):
	"""
	kaldi lattice posteriors to h5features
	this loads everything into memory, but it would be easy to write
	an incremental version if this poses a problem
	"""
	phonemap = k2a.read_kaldi_phonemap(phones_file, word_position_dependent)
	# get order in which phones will be represented in the dimensions of the posteriorgram
	phone_order = get_phone_order(phonemap)
	d = len(phone_order)  # posteriorgram dimension
	# below is basically a parser for kaldi matrix format for each line
	# parse input text file
	with codecs.open(post_file, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()  # xreadlines supposed to be more efficient for large files?
	# here would be nice to use sparse feature format (need to have it in h5features though)
	# might want to begin by using sparse numpy matrix format
	features = []
	utt_ids = []
	times = []
	for index, line in enumerate(lines):
		print("Processing line {0} / {1}".format(index+1, len(lines)))
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
		utt_features = np.zeros(shape=(len(frames), d), dtype=np.float64)
		for f, frame in enumerate(frames):
			assert len(frame) % 2 == 0
			probas = [float(p) for p in frame[1::2]]
			phones = [phonemap[code] for code in frame[::2]]
			# optimisation 1 would be mapping directly a given code to a given posterior dim
			for phone, proba in zip(phones, probas):
				i = phone_order.index(phone)
				# add to previous proba since different variants of a same phone will map to
				# the same dimension i of the posteriorgram
				utt_features[f, i] = utt_features[f, i] + proba
		# normalize posteriorgrams to correct for rounding or thresholding errors
		# by rescaling globally
		total_proba = np.sum(utt_features, axis=1)
		if np.max(np.abs(total_proba-1)) >= 1e-5:  # ad hoc numerical tolerance...
			raise IOError("In utterance {0}, frame {1}: posteriorgram does not sum to one, difference is {2}: ".format(utt_id, f, np.max(np.abs(total_proba-1))))
		utt_features = utt_features/np.tile(total_proba, (d, 1)).T
		features.append(utt_features)
		utt_ids.append(utt_id)
		# as in kaldi2abkhazia, this is ad hoc and has not been checked formally
		times.append(0.0125 + 0.01*np.arange(len(frames)))
	h5features.write(out_file, 'features', utt_ids, times, features)


def features2features(in_file, out_file):
	"""
	kaldi input features (mfcc, etc.) to h5features
	this loads everything into memory, but it would be easy to write
	an incremental version if this poses a problem
	Input features must be in a single archive text format, that can be
	obtained using the 'copy-feats' kaldi utility
	"""
	# below is basically a parser for kaldi vector format for each line
	# parse input text file
	outside_utt = True
	features = []
	utt_ids = []
	times = []
	with codecs.open(in_file, mode='r', encoding='UTF-8') as inp:
		for index, line in enumerate(inp):
			print("Processing line {0}".format(index+1))  # / {1}".format(index+1, len(lines)))
			tokens = line.strip().split(u" ")
			if outside_utt:
				assert len(tokens) == 3 and tokens[1] == u"" and tokens[2] == u"["
				utt_id = tokens[0]
				outside_utt = False
				frames = []
			else:
				if tokens[-1] == u"]":
					# end of utterance
					outside_utt = True
					tokens = tokens[:-1]
				frames.append(np.array(tokens, dtype=np.float))
				if outside_utt:
					# end of utterance, continued
					features.append(np.row_stack(frames))
					# as in kaldi2abkhazia, this is ad hoc and has not been checked formally
					times.append(0.0125 + 0.01*np.arange(len(frames)))
					utt_ids.append(utt_id)
	h5features.write(out_file, 'features', utt_ids, times, features)


# impact of acoustic_scale param ???

#root = "/Users/Thomas/Documents/PhD/Recherche/test"
#phones_file = os.path.join(root, 'phones_CSJ.txt')  # the phones used to train the model
#post_file = os.path.join(root, 'train_CSJ_test_WSJ.post')
#out_file = os.path.join(root, 'train_CSJ_test_WSJ_post.features')
#lattice2features(phones_file, post_file, out_file)


# ad hoc command line
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('phones_file')
    parser.add_argument('post_file')
    parser.add_argument('out_file')
    args = parser.parse_args()
    lattice2features(args.phones_file, args.post_file, args.out_file)

"""
root = "/Users/thomas/Documents/PhD/Recherche/test/"
in_file = p.join(root, 'feat_GPV.ark')
out_file = p.join(root, 'feat_GPV.features')
features2features(in_file, out_file)
"""

"""
root = "/fhgfs/bootphon/scratch/thomas/abkhazia/kaldi"
abx_root = "/fhgfs/bootphon/scratch/thomas/abkhazia/ABXpy"

corpus = "WSJ_main_read"
recipe_dir = p.join(root, corpus, "train_and_decode", "s5")
phones_file = p.join(recipe_dir, "data", "phone_bigram", "phones.txt")
# Eng on WSJ
post_file = p.join(recipe_dir, "export", "phone_bigram_phone_post.post")
out_file = p.join(abx_root, 'Eng_on_WSJ_phone_bigram_post.features')
lattice2features(phones_file, post_file, out_file)
"""
"""
# Eng on CSJ
post_file = p.join(recipe_dir, "export", "phone_bigram_phone_post_CSJ.post")
out_file = p.join(abx_root, 'Eng_on_CSJ_phone_bigram_post.features')
lattice2features(phones_file, post_file, out_file)
"""

"""
corpus = "CSJ_core_laymen"
recipe_dir = p.join(root, corpus, "train_and_decode", "s5")
phones_file = p.join(recipe_dir, "data", "phone_bigram", "phones.txt")
# Eng on WSJ
post_file = p.join(recipe_dir, "export", "phone_bigram_phone_post_WSJ.post")
out_file = p.join(abx_root, 'Jap_on_WSJ_phone_bigram_post.features')
lattice2features(phones_file, post_file, out_file)
"""
"""
corpus = "Buckeye"
recipe_dir = p.join(root, corpus, "train_and_decode", "s5")
phones_file = p.join(recipe_dir, "data", "phone_bigram", "phones.txt")
# Eng on WSJ
post_file = p.join(recipe_dir, "export", "phone_bigram_phone_post_WSJ.post")
out_file = p.join(abx_root, 'BuckeyeEng_on_WSJ_phone_bigram_post.features')
lattice2features(phones_file, post_file, out_file)
"""
#out_file = os.path.join(root, 'trans.features')
#tra_file = os.path.join(root, 'forced_alignment.tra')
#transcription2features(phones_file, tra_file, out_file)
