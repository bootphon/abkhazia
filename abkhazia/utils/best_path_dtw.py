# Copyright 2015, 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.
""" Return the best dtw path"""

import abkhazia.utils as utils
import os
import sys
import numpy as np
from operator import itemgetter



def dtw(alignment, list_phones, word_pos, utt_align):
    """ Get the best path from dtw"""
    """ This was created to get the """
    """ word alignment from the phone level alignment"""
    
    # return if alignment of list of phones is empty 
    # (can happen if utterance is just noise for example)
    if (len(alignment) == 0) or (len(list_phones) == 0):
        return []
    word_alignment = []

    # init dtw matrix
    dtw = np.zeros((len(alignment),len(list_phones)))
    dtw[0,:] = np.inf
    dtw[:,0] = np.inf
    dtw[0,0] = 0

    # compute dtw costs
    for i in range(1,len(alignment)):
        for j in range(1,len(list_phones)):
            cost = int(not alignment[i] == list_phones[j])
            dtw[i,j] = cost + min([dtw[i-1,j], dtw[i,j-1], dtw[i-1, j-1]])
    word_alignment.append(word_pos[-1])

    # go backward to get the best path
    i = len(alignment) - 1
    j = len(list_phones) - 1
    path = []
    while (not i == 0 and not j == 0):
        options = [dtw[i-1,j], dtw[i,j-1], dtw[i-1, j-1]]
        idx, val = min(enumerate(options), key=itemgetter(1))
        if idx == 0:
            i = i-1
            word_alignment.append(word_pos[j])
            path.append((i,j,word_pos[j]))
            continue
        elif idx == 1:
            word_alignment.pop()
            word_alignment.append(word_pos[j-1])
            j = j-1
            path.append((i,j,word_pos[j]))
            continue
        elif idx == 2:
            word_alignment.append(word_pos[j-1])
            i = i-1
            j = j-1
            path.append((i,j,word_pos[j]))
            continue

    # return alignment with words
    word_alignment.reverse()

    prev_word = ''
    complete_alignment = []
    for utt,word in zip(utt_align, word_alignment):
        if word == prev_word:
            prev_word = word
            complete_alignment.append(utt)
            continue
        else:
            prev_word = word
            complete_alignment.append(u'{} {}'.format(utt,word))

    #complete_alignment = ['{} {}'.format(utt,word)
    #        for utt, word in zip(utt_align,word_alignment)]
    return complete_alignment

