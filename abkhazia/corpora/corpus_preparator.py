"""Provides a base class for corpora preparation in the abkhazia format

Copyright (C) 2015, 2016 by Thomas Schatz, Xuan Nga Cao, Mathieu Bernard

"""

import argparse
import os
import re
import codecs
import shutil

import corpus_validation

class AbstractPreparator(object):
    """This class is a common wrapper to all the data preparation scripts.

    The successive steps are:


    2. Link speech folder to the data kaldi directory, optionnaly
        rename the wav files

    3. Create utterance files: It contains the list of all utterances
        with the name of the associated wavefiles, and if there is
        more than one utterance per file, the start and end of the
        utterance in that wavefile expressed in seconds.
        "segments.txt": <utterance-id> <wav-filename> <segment-begin>
        <segment-end>

    4. Create speaker file: It contains the list of all utterances
         with a unique identifier for the associated speaker.
         "utt2spk.txt": <utterance-id> <speaker-id>

    5. Create transcription file: It constains the transcription in
        word units for each utterance "text.txt": <utterance-id>
        <word1> <word2> ... <wordn>

    6. Create phonetic dictionary file: The phonetic dictionary
        contains a list of words with their phonetic transcription,
        "lexicon.txt": <word> <phone_1> <phone_2> ... <phone_n>

    7. Create phone list file: The phone inventory contains a list of
        each symbol used in the pronunciation dictionary,
        "phones.txt": <phone-symbol> <ipa-symbol>


    For more details on data preparation, please refer to
    https://github.com/bootphon/abkhazia/wiki/data_preparation

    """
    def __init__(self, input_dir, output_dir):
        if not os.path.isdir(input_dir):
            raise IOError(
                'input directory does not exist: {}'.format(input_dir))
        self.input_dir = input_dir

        if os.path.exists(output_dir):
            raise IOError(
                'output directory already exists: {}'.format(output_dir))
        self.output_dir = output_dir

        self.data_dir = os.path.join(self.output_dir, 'data')
        self.wavs_dir = os.path.join(self.data_dir, 'wavs')
        self.logs_dir = os.path.join(self.data_dir, 'logs')

    def prepare(self):
        self._1_prepare_output_dir()
        self._2_link_wavs()
        self._3_make_segment()
        self._4_make_speaker()
        self._5_make_transcription()
        self._6_make_lexicon()
        self._7_make_phones()

    def validate(self, verbose=False):
        corpus_validation.validate(self.output_dir, verbose)

    def _1_prepare_output_dir(self):
        """Create an empty output directory hierarchy"""
        os.makedirs(self.wavs_dir)
        os.makedirs(self.logs_dir)

    def _2_link_wavs(self):
        raise NotImplementedError

    def _3_make_segment(self):
        raise NotImplementedError

    def _4_make_speaker(self):
        raise NotImplementedError

    def _5_make_transcription(self):
        raise NotImplementedError

    def _6_make_lexicon(self):
        raise NotImplementedError

    def _7_make_phones(self):
        raise NotImplementedError
