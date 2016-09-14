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
"""Create ABXpy item files from abkhazia corpora"""

from itertools import groupby, chain

import abkhazia.utils as utils
import joblib


def alignment2item(corpus, alignment_file, item_file,
                   segment_extension='single_phone',
                   exclude_phones=[], njobs=1, verbose=0):
    """Creates an item file suitable for most standard ABX tasks on speech corpora

    * The item file is computed from a corpus and an alignment
      file. Each line of the item file have the following structure:

          #file onset offset #phone prev-phone next-phone speaker

    * Onset and offset times are relative to the beginning of the
      utterance, not relative to the times in the wav file.

    * Features for use with this item file should be in h5features
      format with one internal file by utterance (using the
      utterance-id as filename) and times given relative to the
      beginning of the utterance. Given features computed with
      abkhazia (and summarized in a Kaldi scp file), export them in
      h5features using the function abkhazia.utils.kaldi.scp_to_h5f

    TODO this is for 'phone' or 'triphone' tasks, what about tasks on
    whole words?

    Parameters:
    -----------

    corpus (abkhazia.corpus.Corpus): the speech corpus from which the
        alignment have been computed

    alignment_file (filename): the alignment to read from. Must be in the
        abkhazia format, with each line formatted as:

           utt_id tstart tstop phone

        Any utterance present in the alignment but not registered in
        the corpus is ignored

    item_file (filename): the item file to write

    segment_extension (str): can be 'single_phone' (each item
        correspond to a portion of signal corresponding to a single
        phone), 'triphone' (each item correspond to a portion of
        signal corresponding to three consecutive phones),
        'half_triphone' (each item correspond to a portion of signal
        corresponding to a phone with half the preceding and half the
        following phones). Note that none of these affects the content
        of the 'context' column in the output file, only the
        timestamps differ.

    exclude_phones (list): list of phones to exclude from the item
        file, as main or context phones)

    njobs (int): number of parallelized subjobs

    verbose (int): degree of joblib verbosity, more than 10 reports
        all the parallel tasks

    Raise:
    ------

    Raise AssertionError if `segment_extension` is not
    'single_phone', 'triphone' or 'half_triphone'

    """
    assert segment_extension in ('single_phone', 'triphone', 'half_triphone')

    # gather and process each aligned utterance in parallel
    items = joblib.Parallel(
        n_jobs=njobs, verbose=verbose, backend='threading')(
        joblib.delayed(_utt2item)
        (utt_id, corpus, list(lines), segment_extension, exclude_phones)
        for utt_id, lines in groupby(
                utils.open_utf8(alignment_file, mode='r'),
                lambda line: line.split()[0]))

    # open output file and write items to it
    with utils.open_utf8(item_file, mode='w') as fout:
        fout.write('#file onset offset #phone prev-phone next-phone speaker\n')
        fout.write('\n'.join(item for item in chain(*items)) + '\n')


def _utt2item(utt_id, corpus, lines, segment_extension, exclude_phones):
    """Convert an utterance alignment to a list of items"""
    items = []

    # ensure the utterance is registered in the corpus
    if utt_id not in corpus.utts():
        return items

    # get back the utterance's speaker
    speaker = corpus.utt2spk[utt_id]

    # use the first phone only in 'single_phone' case
    if segment_extension == 'single_phone':
        start, stop, phone = lines[0].split()[1:]
        prev_phone = 'SIL'
        next_phone = 'SIL' if len(lines) == 1 else lines[1].split()[3]

        _append_item(items, corpus, utt_id, start, stop, phone,
                     'SIL', next_phone, speaker, exclude_phones)

    # middle lines
    for prev_line, line, next_line in zip(
            lines[:-2], lines[1:-1], lines[2:]):
        prev_start, prev_stop, prev_phone = prev_line.split()[1:]
        start, stop, phone = line.split()[1:]
        next_start, next_stop, next_phone = next_line.split()[1:]

        # setup start and stop according to the segment
        # extension
        if segment_extension == 'triphone':
            start = prev_start
            stop = next_stop
        elif segment_extension == 'half_triphone':
            start = (prev_start + start)/2.
            stop = (stop + next_stop)/2.

        _append_item(items, corpus, utt_id, start, stop, phone,
                     prev_phone, next_phone, speaker, exclude_phones)

    # use the last line only in 'single_phone' case (dont process
    # twice the same line as first and last line)
    if segment_extension == 'single_phone' and len(lines) > 1:
        start, stop, phone = lines[-1].split()[1:]
        prev_phone = lines[-2].split()[3]

        _append_item(items, corpus, utt_id, start, stop, phone,
                     prev_phone, 'SIL', speaker, exclude_phones)

    return items


def _append_item(items, corpus, utt_id, start, stop, phone,
                 prev_phone, next_phone, speaker, exclude_phones):
    """Append a new item to items if its phones are not excluded"""
    if exclude_phones is [] or all(
            p not in exclude_phones
            for p in (prev_phone, phone, next_phone)):
        # get the start time of the utterance in its wav
        _, utt_tstart, _ = corpus.segments[utt_id]
        if utt_tstart is None:
            utt_tstart = 0

        # make phone times relative to utterance (was relative to wav)
        start = str(float(start) - utt_tstart)
        # TODO this is a bug on buckeye manual alignments
        assert float(start) >= 0
        stop = str(float(stop) - utt_tstart)

        # add the new item
        items.append(' '.join(
            [utt_id, start, stop, phone,
             prev_phone, next_phone, speaker]))
