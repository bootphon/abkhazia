# coding: utf-8
# Copyright 2017 Xuan-Nga Cao, Mathieu Bernard
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

"""Data preparation for the Wolof Data

Collected by Elodie Gauthier & Pascal Uriel Elingui
Prepared by Elodie Gauthier & Laurent Besacier
GETALP LIG, Grenoble, France & Voxygen SAS, Dakar, Sénégal

Overview
--------

The package contains Wolof speech corpus with audio data in the
directory data/. The data directory contains 6 subdirectories:

  * train - speech data and transcription for training automatic
      speech recognition system (Kaldi ASR format 1 )

  * dev - speech data and transcription (verified) to evaluate the ASR
      system (Kaldi ASR format)

  * test - speech data and transcription (verified) for testing the
      ASR system (Kaldi ASR format)

  * dev_unverified - original speech data and transcription (NOT
      verified, contains mispronunciations)

  * test_unverified - original speech data and transcription (NOT
      verified, contains mispronunciations)

  * local - for now, contains the Wolof vocabulary (without
      length-contrasted units). Once you will ran the run.sh script it
      will contain the dict/ and lang/ directories needed to build the
      ASR system.

LM/ directory contains 2 text corpus, the language model and its
perplexity computed from the dev and test datasets.

Publication on Wolof speech & LM data
-------------------------------------


"""

import os
import re
import shutil

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparator


class WolofPreparator(AbstractPreparator):
    """Convert the Wolof speech corpus to the abkhazia format"""

    name = 'wolof'

    url = 'https://github.com/besacier/ALFFA_PUBLIC/tree/master/ASR/WOLOF'

    audio_format = 'wav'

    description = 'collection of Wolof speech data'

    long_description = '''
    The corpus is freely available at the github URL above. More
    details on the corpus and how it was collected can be found on the
    following publication (please cite this bibtex if you use this
    data).

    @inproceedings{gauthier2016collecting,
      title={Collecting resources in sub-saharan african languages for
        automatic speech recognition: a case study of wolof},
      author={Gauthier, Elodie and Besacier, Laurent and Voisin, Sylvie
        and Melese, Michael and Elingui, Uriel Pascal},
      year={2016},
      organization={LREC}}'''

    silences = ['sil']

    variants = []

    def __init__(self, input_dir, log=utils.logger.null_logger(),
                 copy_wavs=False):
        super(WolofPreparator, self).__init__(input_dir, log=log)
        self.copy_wavs = copy_wavs

        # list all the wav file in the corpus
        self.wav_files = []
        for dirpath, dirs, files in os.walk(self.input_dir):
            for f in files:
                m_file = re.match("^(.*)\.wav$", f)
                if m_file:
                    self.wav_files.append(os.path.join(dirpath, f))

        self.phones = self._make_phones()


    def list_audio_files(self):
        return self.wav_files

    def make_segment(self):
        segments = dict()
        for wav_file in self.wav_files:
            utt_id = os.path.splitext(os.path.basename(wav_file))[0]
            segments[utt_id] = (utt_id, None, None)
        return segments

    def make_speaker(self):
        utt2spk = dict()
        for wav_file in self.wav_files:
            utt_id = os.path.splitext(os.path.basename(wav_file))[0]
            match_line = re.match("(WOL.*)_(.*)_(.*)", utt_id)
            if match_line:
                speaker_id = match_line.group(1)
                utt2spk[utt_id] = speaker_id
        return utt2spk

    def make_transcription(self):
        text = dict()
        for line in open(os.path.join(self.input_dir, "text"), 'r'):
            k, v = line.strip().split('  ', 1)
            text[k] = v
        return text

    def make_lexicon(self):
        lexicon = dict()
        infile = open(os.path.join(self.input_dir, "lexicon.txt"), 'r')
        for line in infile:
            try:
                k, v = line.strip().split('\t', 1)
            except ValueError:
                l = line.split(' ')
                k = l[0]
                v = l[1:]
            lexicon[k] = v
        return lexicon

    def _make_phones(self):
        phones = set()
        for line in open(os.path.join(self.input_dir, "lexicon.txt"), 'r'):
            m = re.match("(.*)\t(.*)", line)
            if m:
                phn = m.group(2)
                for p in phn.split(' '):
                    phones.add(p)

        return {v: v for v in phones}
