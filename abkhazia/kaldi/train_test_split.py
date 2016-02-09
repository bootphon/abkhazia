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
"""

import os.path as p
import random
import os
import shutil
import abkhazia.utilities.basic_io as io


def train_test_split(corpus_path, split_speakers=False,
				train_amount=None,
				train_proportion=None,
				train_speakers=None,
				train_name="train", test_name="test"):
	"""
	Separate the utterances in a corpus in abkhazia format into
	a train set and a test set. The results are put in a subfolder
	of the 'data' directory of the corpus named 'split'

	Only one of train_amount, train_proportion and train_speakers
	can be set at the same time (default is train_proportion=0.5)
	train_speakers cannot be set if split_speakers is True

	If the split_speakers argument is False,
	the data for each speaker is attributed to one of the
	two sets as a whole.
	If train_speakers is set, it determines which speaker
	goes in which set.
	Otherwise train_amount (or a proportion train_proportion)
	of the speakers are randomly selected to be in the
	training set. Note that this might not be appropriate
	when the amount of utterances available per speaker
	is too unbalanced.

	If the split_speakers argument is True,
	both sets get speech from all the speakers
	with a number of utterances by speaker in each set
	matching the number of utterances by speaker in the
	whole corpus.
	The total number of utterances in the training set
	is equal to either train_amount or
	round(train_proportion*total_nb_utt).
	"""
	""" parse arguments """
	assert p.isdir(corpus_path), "{0} is not a directory".format(corpus_path)
	data_dir = p.join(corpus_path, 'data')
	assert p.isdir(data_dir), "{0} is not a directory".format(data_dir)
	split_dir = p.join(data_dir, 'split')
	if not(p.isdir(split_dir)):
		os.mkdir(split_dir)
	train_dir = p.join(split_dir, train_name)
	test_dir = p.join(split_dir, test_name)
	if p.isdir(train_dir):
		raise ValueError("There is already a split called: {0}".format(train_dir))
	else:
		os.mkdir(train_dir)
	if p.isdir(test_dir):
		raise ValueError("There is already a split called: {0}".format(test_dir))
	else:
		os.mkdir(test_dir)
	# all we need is the utt2spk.txt file
	utt2spk_file = p.join(data_dir, 'utt2spk.txt')
	assert p.exists(utt2spk_file), "{0} file does not exist".format(utt2spk_file)
	sp = not(train_speakers is None)
	am = not(train_amount is None)
	pr = not(train_proportion is None)
	if (sp and am) or (sp and pr) or (am and pr):
		raise ValueError("Specify only one of train_amount, train_proportion and train_speakers")
	if not(sp) and not(am) and not(pr):
		pr = True
		train_proportion = .5
	""" read input """
	utt_ids, utt_speakers = io.read_utt2spk(p.join(corpus_path, 'data', 'utt2spk.txt'))
	utts = zip(utt_ids, utt_speakers)
	nb_utts = len(utt_ids)
	speakers =	set(utt_speakers)
	""" split utterances """
	train_utt_ids, test_utt_ids = [], []
	if split_speakers:
		assert not(sp), \
			"When split_speakers is set to True, the train_speakers argument cannot be used"
		proportion = train_proportion if pr else int(round(train_amount/float(nb_utts)))
		for speaker in speakers:
			spk_utts = \
				[utt_id for utt_id, utt_speaker in utts \
					if utt_speaker == speaker]
			assert len(spk_utts) > 1, \
				"Speaker {0} has only {1} sentence".format(speaker, len(spk_utts))
			n_train = int(round(len(spk_utts)*proportion))
			assert n_train < len(spk_utts), \
				(
				"Your choice of parameters yields a test set without any sentence "
				"from speaker {0}"
				).format(speaker)
			assert n_train > 0, \
				(
				"Your choice of parameters yields a train set without any sentence "
				"from speaker {0}"
				).format(speaker)
			# sample train and test utterances at random for this speaker
			train_utts = random.sample(spk_utts, n_train)
			test_utts = list(set.difference(set(spk_utts), set(train_utts)))
			# add to train and test sets
			train_utt_ids = train_utt_ids + train_utts
			test_utt_ids = test_utt_ids + test_utts
	else:
		if am or pr:
			amount = train_amount if am else int(round(train_proportion*len(speakers)))
			assert amount > 0, "Your choice of parameters yields an empty train-set"
			assert amount < len(speakers), "Your choice of parameters yields an empty test-set"
			speaker_list = list(speakers)
			random.shuffle(speaker_list)
			train_speakers = speaker_list[:amount]
		else:
			missing_speakers = [spk for spk in train_speakers if not(spk in speakers)]
			assert not(missing_speakers), \
				(
				"The following speakers specified in train_speakers "
				"are not found in the corpus: {0}"
				).format(missing_speakers)
		for speaker in speakers:
			spk_utts = \
				[utt_id for utt_id, utt_speaker in utts \
					if utt_speaker == speaker]
			if speaker in train_speakers:
				train_utt_ids = train_utt_ids + spk_utts
			else:
				test_utt_ids = test_utt_ids + spk_utts
	""" write output and cpp sort the files """
	files= ['utt2spk.txt', 'text.txt', 'segments.txt']
	try:
		# select relevant parts of utt2spk.txt, text.txt and segments.txt
		for f in files:
                  train_out, test_out = p.join(train_dir, f), p.join(test_dir, f)
                  io.copy_first_col_matches(p.join(data_dir, f), train_out, train_utt_ids)
                  io.copy_first_col_matches(p.join(data_dir, f), test_out, test_utt_ids)
                  io.cpp_sort(train_out)
                  io.cpp_sort(test_out)
	except:
		try:
			shutil.rmtree(train_dir)
		except:
			pass
		try:
			shutil.rmtree(test_dir)
		except:
			pass
		raise
