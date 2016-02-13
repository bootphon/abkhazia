#!/usr/bin/env python
# coding: utf-8
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

"""Data preparation for the LibriSpeech corpus

The raw distribution of LibriSpeech is available at
http://www.openslr.org/12/

The LibriSpeech dictionary is available for download at
http://www.openslr.org/resources/11/librispeech-lexicon.txt

"""

import os
import re

from abkhazia.utils import list_files_with_extension
from abkhazia.corpora.utils import (
    AbstractPreparatorWithCMU, default_argument_parser, DEFAULT_OUTPUT_DIR)

class LibriSpeechPreparator(AbstractPreparatorWithCMU):
    """Convert the LibriSpeech corpus to the abkhazia format"""
    name = 'LibriSpeech'

    audio_format = 'flac'

    phones = {
        'IY': u'iː',
        'IH': u'ɪ',
        'EH': u'ɛ',
        'EY': u'eɪ',
        'AE': u'æ',
        'AA': u'ɑː',
        'AW': u'aʊ',
        'AY': u'aɪ',
        'AH': u'ʌ',
        'AO': u'ɔː',
        'OY': u'ɔɪ',
        'OW': u'oʊ',
        'UH': u'ʊ',
        'UW': u'uː',
        'ER': u'ɝ',
        'JH': u'ʤ',
        'CH': u'ʧ',
        'B': u'b',
        'D': u'd',
        'G': u'g',
        'P': u'p',
        'T': u't',
        'K': u'k',
        'S': u's',
        'SH': u'ʃ',
        'Z': u'z',
        'ZH': u'ʒ',
        'F': u'f',
        'TH': u'θ',
        'V': u'v',
        'DH': u'ð',
        'M': u'm',
        'N': u'n',
        'NG': u'ŋ',
        'L': u'l',
        'R': u'r',
        'W': u'w',
        'Y': u'j',
        'HH': u'h',
    }

    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    def __init__(self, input_dir, selection=None,
                 librispeech_dict=None, cmu_dict=None,
                 output_dir=None, verbose=False, njobs=1):

        # guess librispeech dictionary if not specified, look for it
        # in the Librispeech root directory
        if librispeech_dict is None:
            librispeech_dict = os.path.join(
                input_dir, 'librispeech-lexicon.txt')

        # init path to LibriSpeech dictionary
        if not os.path.isfile(librispeech_dict):
            raise IOError(
                'LibriSpeech dictionary does not exist: {}'
                .format(librispeech_dict))
        self.librispeech_dict = librispeech_dict

        # update name, input and output directories if a subpart
        # selection is specified
        if selection is not None:
            self.name += '-' + selection
            input_dir = os.path.join(input_dir, selection)
            # if output_dir is None:
            #     output_dir = os.path.join(DEFAULT_OUTPUT_DIR, self.name)
            # output_dir += '-' + selection

        # call the AbstractPreparatorWithCMU __init__
        super(LibriSpeechPreparator, self).__init__(
            input_dir, cmu_dict, output_dir, verbose, njobs)


    def list_audio_files(self):
        flacs = list_files_with_extension(self.input_dir, '.flac', abspath=True)

        wavs = []
        for flac in flacs:
            utt_id = os.path.basename(flac).replace('.flac', '')
            len_sid = len(utt_id.split('-')[0])  # length of speaker_id
            prefix = '00' if len_sid == 2 else '0' if len_sid == 3 else ''
            wavs.append(prefix + utt_id + '.wav')

        return flacs, wavs

    def make_segment(self):
        with open(self.segments_file, 'w') as outfile:
            for wav_file in list_files_with_extension(self.wavs_dir, '.wav'):
                bname = os.path.basename(wav_file)
                utt_id = bname.replace('.wav', '')
                outfile.write(utt_id + ' ' + bname + '\n')
        self.log.debug('finished creating segments file')

    def make_speaker(self):
        with open(self.speaker_file, 'w') as outfile:
            for wav in list_files_with_extension(self.wavs_dir, '.wav'):
                bname = os.path.basename(wav)
                utt_id = bname.replace('.wav', '')
                speaker_id = bname.split("-")[0]
                outfile.write(utt_id + ' ' + speaker_id + '\n')
        self.log.debug('finished creating utt2spk file')

    def make_transcription(self):
        corrupted_wavs = os.path.join(self.logs_dir, 'corrupted_wavs.txt')

        outfile = open(self.transcription_file, "w")
        outfile2 = open(corrupted_wavs, "w")

        wav_list = [os.path.basename(w).replace('.wav', '') for w in
                    list_files_with_extension(self.wavs_dir, '.wav')]

        for trs_file in list_files_with_extension(self.input_dir, '.trans.txt'):
            # for each line of transcript, convert the utt_ID to
            # normalize speaker_ID and check if wav file exists; if
            # not, output corrputed files to corrupted_wavs.txt, else
            # output text.txt
            for line in open(trs_file):
                matched = re.match(r'([0-9\-]+)\s([A-Z].*)', line)
                if matched:
                    utt_id = matched.group(1)
                    speaker_id = utt_id.split("-")[0]
                    utt = matched.group(2)

                    # TODO refactor this
                    if len(speaker_id) == 2:
                        new_utt_id = "00" + utt_id
                        if new_utt_id in wav_list:
                            outfile.write(new_utt_id + ' ' + utt + '\n')
                        else:
                            outfile2.write(new_utt_id + '.wav\n')
                    elif len(speaker_id) == 3:
                        new_utt_id = "0" + utt_id
                        if new_utt_id in wav_list:
                            outfile.write(new_utt_id + ' ' + utt + '\n')
                        else:
                            outfile2.write(new_utt_id + '.wav\n')
                    else:
                        if utt_id in wav_list:
                            outfile.write(utt_id + ' ' + utt + '\n')
                        else:
                            outfile2.write(utt_id + '.wav\n')

        self.log.debug('finished creating text file')

    def make_lexicon(self):
        # To generate the lexicon, we will use the cmu dict and the
        # dict of OOVs generated by LibriSpeech)
        cmu_combined = {}

        with open(self.librispeech_dict, 'r') as infile:
            for line in infile:
                if not re.match(";;; ", line):
                    dictionary = re.match("(.*)\t(.*)", line)
                    if dictionary:
                        entry = dictionary.group(1)
                        phn = dictionary.group(2)
                        # remove pronunciation variants
                        phn = phn.replace("0", "")
                        phn = phn.replace("1", "")
                        phn = phn.replace("2", "")
                        # create the combined dictionary
                        cmu_combined[entry] = phn

        with open(self.cmu_dict, 'r') as infile:
            for line in infile:
                if not re.match(";;; ", line):
                    dictionary = re.match(r"(.*)\s\s(.*)", line)
                    if dictionary:
                        entry = dictionary.group(1)
                        phn = dictionary.group(2)
                        # remove pronunciation variants
                        phn = phn.replace("0", "")
                        phn = phn.replace("1", "")
                        phn = phn.replace("2", "")
                        # create the combined dictionary
                        cmu_combined[entry] = phn

        # Loop through the words in transcripts by descending
        # frequency and create the lexicon by looking up in the
        # combined dictionary.
        with open(self.lexicon_file, "w") as outfile:
            for word, freq in sorted(cmu_combined.items()):
                outfile.write(word + ' ' + freq + '\n')

        self.log.debug('finished creating lexicon file')


# because LibriSpeech need two dictionary files, we can't use the
# default corpora.utils.main function
def main():
    """The command line entry for the LibriSpeech corpus preparation"""
    try:
        # mapping of the LibriSpeech variations. TODO this is actually
        # hard-coded to present a selection on --help. See if we can
        # parse input_dir instead of this mapping...
        selection = ['dev-clean', 'dev-other',
                     'test-clean', 'test-other',
                     'train-clean-100', 'train-clean-360']

        selection_descr = ', '.join([str(i+1) + ' is ' + selection[i]
                                     for i in range(len(selection))])

        preparator = LibriSpeechPreparator
        parser = default_argument_parser(preparator.name, __doc__)

        parser.add_argument(
            '-s', '--selection', default=None,
            metavar='SELECTION', type=int,
            help='the subpart of LibriSpeech to prepare. If not specified, '
            'prepare the entire corpus. Choose SELECTION in {}. ('
            .format(range(1, len(selection)+1)) + selection_descr + ')')

        parser.add_argument(
            '--cmu-dict', default=None,
            help='the CMU dictionary file to use for lexicon generation. '
            'If not specified use {}'.format(preparator.default_cmu_dict))

        parser.add_argument(
            '-l', '--librispeech-lexicon', default=None,
            help='the librispeech-lexicon.txt file at the root '
            'of the LibriSpeech distribution. '
            'If not specified, guess it from INPUT_DIR')

        # parse command line arguments
        args = parser.parse_args()

        selection = (None if args.selection is None
                     else selection[args.selection-1])

        # prepare the corpus
        corpus_prep = preparator(
            args.input_dir, selection,
            args.cmu_dict, args.librispeech_lexicon,
            args.output_dir, args.verbose, args.njobs)

        corpus_prep.prepare()
        if not args.no_validation:
            corpus_prep.validate()

    except Exception as err:
        print('fatal error: {}'.format(err))
    except KeyboardInterrupt:
        print 'keyboard interruption, exiting'


if __name__ == '__main__':
    main()
