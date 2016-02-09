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

In addition to the LibriSpeech corpus, this preparator need the CMU
and LibriSpeech dictionaries.

The CMU dictionary is available for free at
http://www.speech.cs.cmu.edu/cgi-bin/cmudict. The preparator is
designed for version 0.7a of the CMU dictionary, but other recent
versions could probably be used without changing anything

Complementing the CMU dictionary, the preparator also uses the
LibriSpeech dictionary, which contains the words not found in the CMU
(not exhaustive list however). The LibriSpeech dictionary is available
for download at http://www.openslr.org/resources/11/librispeech-lexicon.txt

As the original speech files in LibriSpeech are encoded in flac, this
preparator convert them to wav. So the 'flac' command must be
available on your system.

This preparator have been tested on 'train-clean-100' and
'train-clean-360' versions of LibriSpeech

"""

import os
import progressbar
import re

from abkhazia.corpora.utils import (
    AbstractPreparator,
    list_files_with_extension,
    flac2wav,
    default_argument_parser
)

# TODO have librispeech_dict as an optionnal argument and guess it
# from input_dir by default (input_dir/../librispeech-lexicon.txt)

# TODO have command-line option --type train-clean-100
class LibriSpeechPreparator(AbstractPreparator):
    """Convert the LibriSpeech corpus to the abkhazia format"""
    name = 'LibriSpeech'

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

    def __init__(self, input_dir, cmu_dict,
                 librispeech_dict=None, output_dir=None, verbose=False):
        # call the AbstractPreparator __init__
        super(LibriSpeechPreparator, self).__init__(
            input_dir, output_dir, verbose)

        # init path to CMU dictionary
        if not os.path.isfile(cmu_dict):
            raise IOError(
                'CMU dictionary does not exist: {}'
                .format(cmu_dict))
        self.cmu_dict = cmu_dict

        # guess librispeech dictionary if not specified
        if librispeech_dict is None:
            librispeech_dict = os.path.join(
                self.input_dir, '..', 'librispeech-lexicon.txt')
            self.log.debug('guessed librispeech dictionary: {}'
                           .format(librispeech_dict))

        # init path to LibriSpeech dictionary
        if not os.path.isfile(librispeech_dict):
            raise IOError(
                'LibriSpeech dictionary does not exist: {}'
                .format(librispeech_dict))
        self.librispeech_dict = librispeech_dict

    # TODO this function can easily be parallelized (using joblib for example)
    def make_wavs(self):
        flacs = list_files_with_extension(self.input_dir, '.flac')
        self.log.info('converting {} flac files to wav...'.format(len(flacs)))

        for flac in progressbar.ProgressBar()(flacs):
            # get the wav name
            utt_id = os.path.basename(flac).replace('.flac', '')
            len_sid = len(utt_id.split('-')[0]) # length of speaker_id
            prefix = '00' if len_sid == 2 else '0' if len_sid == 3 else ''
            wav = os.path.join(self.wavs_dir, prefix + utt_id + '.wav')

            # convert original flac to renamed wav if not exist
            if not os.path.isfile(wav):
                flac2wav(flac, wav)
        self.log.debug('finished linking wav files')

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
            for w, f in sorted(cmu_combined.items()):
                outfile.write(w + ' ' + f + '\n')

        self.log.debug('finished creating lexicon file')


# because LibriSpeech need two dictionary files, we can't use the
# default corpora.utils.main function
def main():
    """The command line entry for the LibriSpeech corpus preparation"""
    try:
        preparator = LibriSpeechPreparator
        parser = default_argument_parser(preparator.name, __doc__)

        parser.add_argument('cmu_dict', help='the CMU dictionary '
                            'file to use for lexicon generation')

        parser.add_argument('-l', '--librispeech-lexicon',
                            default=None,
                            help='the librispeech-lexicon.txt file '
                            'at the root of the LibriSpeech distribution. '
                            'If not specified, guess it from INPUT_DIR')

        # parse command line arguments
        args = parser.parse_args()

        # prepare the corpus
        corpus_prep = preparator(
            args.input_dir, args.cmu_dict,
            args.librispeech_lexicon, args.output_dir, args.verbose)

        corpus_prep.prepare()
        if not args.no_validation:
            corpus_prep.validate()
    except Exception as err:
        print('fatal error: {}'.format(err))


if __name__ == '__main__':
    main()
