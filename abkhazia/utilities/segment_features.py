# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 15:05:38 2014

@author: Thomas Schatz
"""

import abkhazia.utilities.basic_io as basic_io
import h5features
from itertools import groupby


def segment_features(features_file, segments_file, out_file):
	"""
	Segment h5features file containing features for whole wavefiles
	of an abkhazia corpus (or split of a corpus) into features for
	segments as described in the provided segments.txt file.
	"""
	utt_ids, wavefiles, starts, stops = io.read_segments(segments_file)
	if all([e is None for e in starts]) and all([e is None for e in stops]):
		print "Segments already match wavefiles, nothing to segment..."
	else:
		# Group utterances by wavefiles
		data = zip(utt_ids, wavefiles, starts, stops)
		get_wav = lambda e: e[1]
		for wavefile, utts in groupby(data, get_wav):
			# load features for whole wavefile
			xxx = h5features.load()
			for utt_id, _, start, stop in utts:
				# select and output features for appropriate segment

	# 2. for each wavefile load features then iterate on wavs select features
	# based on times and write
	for utt_id, wav, start, stop in :
		# read in original features


# segment_features(...)

# need either buckeye trained or librispeech trained model for control
# need to gather the whole matrix of ABX results + launch ABnet computations 

