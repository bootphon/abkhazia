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

import codecs
from itertools import groupby
import os.path as p
import random

import abkhazia.utilities.basic_io as io

# TODO this is for 'phone' or 'triphone' tasks, what about tasks on
# whole words
def alignment2item(alignment_file, item_file, spk_id_len,
                   segment_extension='single_phone'):
    """Creates an item file suitable for most standard ABX tasks on speech corpora.

    Input is an abkhazia formatted alignment file for a given corpus.
    Output is a .item file suitable for use with ABXpy.

    Features for use with this item file should be in h5features
    format with one internal file by utterance (using the utterance-id
    as filename) and times given relative to the beginning of the
    utterance.

    segment_extension: string, can be 'single_phone' (each item
        correspond to a portion of signal corresponding to a single
        phone), 'triphone' (each item correspond to a portion of
        signal corresponding to three consecutive phones),
        'half_triphone' (each item correspond to a portion of signal
        corresponding to a phone with half the preceding and half the
        following phones). Note that none of these affects the content
        of the 'context' column in the output file, only the
        timestamps differ.

    """
    assert segment_extension in ['single_phone', 'triphone', 'half_triphone']
    # read alignment file
    with codecs.open(alignment_file, mode='r', encoding='UTF-8') as inp:
        all_lines = inp.readlines()
    # open item_file and write to it
    with codecs.open(item_file, mode='w', encoding='UTF-8') as out:
        # write header
        out.write('#file onset offset #phone prev-phone next-phone talker\n')
        # gather and process each utterance independently

        # group by utt_id
        for utt_id, lines in groupby(all_lines,
                                     lambda line: line.split()[0]):

            lines = list(lines)  # convert itertools object into list
            speaker = utt_id[:spk_id_len]
            # use the first phone only in 'single_phone' case
            # FIXME what if the first phone is a SIL
            if segment_extension == 'single_phone':
                _, start, stop, phone = lines[0].split()
                if len(lines) == 1:
                    next = 'SIL'
                else:
                    next = lines[1].split()[3]
                info = [utt_id, start, stop, phone, 'SIL', next, speaker]
                out.write(u" ".join(info) + u"\n")
            # middle lines
            for prev_l, line, next_l in zip(
                            lines[:-2], lines[1:-1], lines[2:]):
                _, prev_start, prev_stop, prev_phone = prev_l.split()
                _, start, stop, phone = line.split()
                _, next_start, next_stop, next_phone = next_l.split()
                if segment_extension == 'triphone':
                    seg_start, seg_stop = prev_start, next_stop
                elif segment_extension == 'half_triphone':
                    seg_start, seg_stop = (prev_start+start)/2., (stop + next_stop)/2.
                else:
                    seg_start, seg_stop = start, stop
                info = [utt_id, seg_start, seg_stop, phone, prev_phone, next_phone, speaker]
                out.write(u" ".join(info) + u"\n")
            # use the last line only in 'single_phone' case
            # FIXME what if the last phone is a SIL
            if segment_extension == 'single_phone':
                # do not process twice the same line as first and last
                # line!
                if len(lines) > 1:
                    _, start, stop, phone = lines[-1].split()
                    prev = lines[-2].split()[3]
                    info = [utt_id, start, stop, phone, prev, 'SIL', speaker]
                    out.write(u" ".join(info) + u"\n")


#TODO put filter_alignment with the functions used for exporting
# results from kaldi to abkhazia ? Or rather as a generic abkahzia utility
def filter_alignment(alignment_file, output_file, segment_file):
    """ Keep alignment tokens if and only if there is an entry
    for the corresponding utterance in the file provided """
    utt_ids, _, _, _ = io.read_segments(segment_file)
    io.copy_first_col_matches(alignment_file, output_file, utt_ids)


def add_segment_info(segment_info_file, item_file_in, item_file_out):
    """
    Add columns indicating C/V/special and tone where applicable
    """
    with codecs.open(segment_info_file, mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()
    symbols, kinds, tones, segments = zip(*[line.strip().split()
                                            for line in lines])

    kinds = {symbol: kind for symbol, kind in zip(symbols, kinds)}
    tones = {symbol: tone for symbol, tone in zip(symbols, tones)}
    segments = {symbol: segment for symbol, segment in zip(symbols, segments)}
    with codecs.open(item_file_in, mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()
    new_lines = [lines[0][:-1] + u' phone-class tone segment\n']
    specials = set()
    for line in lines[1:]:
        phone = line.strip().split()[3]
        kind = kinds[phone]
        tone = tones[phone]
        segment = segments[phone]
        # keep only line with C or V segments (not SIL etc.)
        if not(kind in ['C', 'V']):
            specials.add(phone)
        else:
            new_lines.append(
                    line[:-1] + u' ' + kind + u' ' +
                    tone + u' ' + segment + u'\n')

    with codecs.open(item_file_out, mode='w', encoding='UTF-8') as out:
        for line in new_lines:
            out.write(line)
    print("Removed entries with following central phones: {0}"
          .format(specials))


def remove_bad_phones(bad_phones, item_file_in, item_file_out):
    """
    Remove occurences of the specified phones (as main phone or in context)
    """
    with codecs.open(item_file_in, mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()
    new_lines = [lines[0]]
    n_removed = 0
    for line in lines[1:]:
        phone, prev_phone, next_phone = line.strip().split()[3:6]
        if(phone in bad_phones or
           prev_phone in bad_phones or
           next_phone in bad_phones):
            n_removed = n_removed+1
            continue
        new_lines.append(line)
    with codecs.open(item_file_out, mode='w', encoding='UTF-8') as out:
        for line in new_lines:
            out.write(line)
    print("Removed {0} lines".format(n_removed))


def get_talkers(item_file):
    with codecs.open(item_file, mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()
    talkers = set()
    for line in lines[1:]:
        talkers.add(line.strip().split()[6])
    return talkers


def filter_talkers(item_file, kept_talkers, out_file):
    with codecs.open(item_file, mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()
    new_lines = lines[:1]
    for line in lines[1:]:
        talker = line.strip().split()[6]
        if talker in kept_talkers:
            new_lines.append(line)
    with codecs.open(out_file, mode='w', encoding='UTF-8') as out:
        for line in new_lines:
            out.write(line)


def sample_talkers(item_file, nb_talkers, out_file):
    talkers = get_talkers(item_file)
    talkers = list(talkers)
    random.shuffle(talkers)
    talkers = talkers[:nb_talkers]
    filter_talkers(item_file, talkers, out_file)


def get_item_file(root, corpus, spk_id_len,
                  segment_info_file=None, bad_phones=None):
    alignment = p.join(root, corpus + '_forced_alignment.txt')
    test_utts = p.join(root, corpus + '_test_utts.txt')
    test_alignment = p.join(root, corpus + '_test_forced_alignment.txt')
    filter_alignment(alignment, test_alignment, test_utts)

    item_file = p.join(root, corpus + '_phone.item')
    alignment2item(test_alignment, item_file, spk_id_len, 'single_phone')
    if not(bad_phones is None):
        remove_bad_phones(bad_phones, item_file, item_file)
    if not(segment_info_file is None):
        add_segment_info(segment_info_file, item_file, item_file)

# """
# root='/Users/thomas/Documents/PhD/Recherche/test/'
# item_file = p.join(root, 'WSJ_phone_threshold_1_5.item')
# sample_talkers(item_file, 5, p.join(root, 'WSJ_phone_threshold_1_5-small.item'))
# """

root = '/Users/thomas/Documents/PhD/Recherche/test/'
corpus = 'BUC'
# TODO get this from spk2utt and replace explicitly given segment file
# by path to an abkhazia split
spk_id_len = 3

get_item_file(root, corpus, spk_id_len, p.join(
        root, 'segment_info_' + corpus + '.txt'))

# get_item_file(root, corpus, spk_id_len, p.join(root, 'segment_info_'
#     + corpus + '.txt'), ['zy:', 'F:', 'd:', 'g:', 's:'])
#     get_item_file(root, 'CSJ', 5) get_item_file(root, 'WSJ', 3)
