# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 15:05:38 2014

@author: Thomas Schatz
"""

import abkhazia.utilities.basic_io as io
import h5features
from itertools import groupby
import os
import numpy as np


def segment_features(features_file, segments_file, out_file):
	"""
	Segment h5features file containing features for whole wavefiles
	of an abkhazia corpus (or split of a corpus) into features for
	segments as described in the provided segments.txt file.
	"""
	utt_ids, wavefiles, starts, stops = io.read_segments(segments_file)
	if all([e is None for e in starts]) and all([e is None for e in stops]):
		#TODO use a log instead of a print statement
		print "segment_features: segments already match wavefiles, doing nothing..."
	else:
		# Group utterances by wavefiles
		data = zip(utt_ids, wavefiles, starts, stops)
		get_wav = lambda e: e[1]
		for wavefile, utts in groupby(data, get_wav):
			# load features for whole wavefile
			wav_id = os.path.splitext(wavefile)[0]
			times, features = h5features.read(features_file, from_internal_file=wav_id)
			times, features = times[wav_id], features[wav_id]  # no need for dict here
			utt_ids, utt_times, utt_features = [], [], []	
			for utt_id, _, start, stop in utts:
				# select features for appropriate segment
				utt_ids.append(utt_id)
				indices = np.where(np.logical_and(times >= start, times <= stop))[0]
				if indices.size() == 0:
					print start
					print stop
					print times
				utt_times = times[indices] - start  # get times relative to beginning of utterance
				utt_features.append(features[indices,:])
			# write to out_file once for each wavefile
			h5features.write(out_file, 'features', utt_ids, utt_times, utt_features)

