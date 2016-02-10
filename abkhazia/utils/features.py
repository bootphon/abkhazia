# -*- coding: utf-8 -*-
# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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


import h5features
from itertools import groupby
import numpy as np
import os

import abkhazia.utils.basic_io as io


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
        for wav, utts in groupby(data, get_wav):
            #TODO use a log instead of a print statement
            print "Segmenting features for file {} by utterance".format(wav)
            # load features for whole wavefile
            wav_id = os.path.splitext(wav)[0]
            # TODO fix that
            times, features = h5features.read(
                    features_file, from_internal_file=wav_id)
            # no need for dict here
            times, features = times[wav_id], features[wav_id]

            utt_ids, utt_times, utt_features = [], [], []
            for utt_id, _, start, stop in utts:
                # select features for appropriate segment
                utt_ids.append(utt_id)
                indices = np.where(np.logical_and(times >= start, times <= stop))[0]
                # get times relative to beginning of utterance
                utt_times.append(times[indices] - start)
                utt_features.append(features[indices, :])
            # write to out_file once for each wavefile
            h5features.write(out_file, 'features', utt_ids, utt_times, utt_features)
