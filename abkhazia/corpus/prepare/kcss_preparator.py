# coding: utf-8

# Copyright 2018 Xuan-Nga Cao, Mathieu Bernard
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
"""Data preparation for the Korean Corpus of Spontaneous Speech"""


# Le second est je pense un problème d'unicode car ce problème
# n'arrive qu'avec certains fichiers et pas à tous. Pour la 1ère
# uttérance, pour certains fichiers, il prend toutes les lignes du
# fichier (qui comprend toutes les uttérances). Pour les autres
# uttérances, je n'ai pas ce problème. Et ça n'arrive qu'à certains
# fichiers et pas à tous.  Un exemple de problème:
# s04m15m3.TextGrid. Un qui marche ok: s40f43f6.TextGrid

# Aussi, je ne sais pas si ça va créer un problème dans la validation
# d'abkhazia mais les fichiers générés par mon script sont en
# utf-16-be (qui est l'encodage original des fichiers TextGrid).


import codecs
import os
import progressbar

import abkhazia.utils as utils
from abkhazia.utils.textgrid import TextGrid
from abkhazia.corpus.prepare import AbstractPreparator


class KCSSPreparator(AbstractPreparator):
    """Convert the KCSS corpus to the abkhazia format"""
    name = 'kcss'

    url = 'http://dx.doi.org/10.13064/KSSS.2015.7.2.103'

    audio_format = 'wav'

    description = 'Korean Corpus of Spontaneous Speech'

    long_description = '''
    The data are freely available to the research community. This
    database consists of 40 hours of sponteaneous speech recorded from
    40 participants. Inspired by the Buckeye corpus.'''

    phones = {
        'p0': u'p',
        'ph': u'pʰ',
        'pp': u'p*',
        't0': u't',
        'th': u'tʰ',
        'tt': u't*',
        'k0': u'k',
        'kh': u'kʰ',
        'kk': u'k*',
        'll': u'l',
        's0': u's',
        'ss': u's*',
        'hh': u'h',
        'c0': u'ʨ',
        'ch': u'ʨʰ',
        'cc': u'ʨ*',
        'mm': u'm',
        'nn': u'n',
        'ng': u'ŋ',
        'ii': u'i',
        'ye': u'je',
        'ee': u'e',
        'ya': u'ja',
        'aa': u'a',
        'yv': u'jə',
        'xx': u'ɨ',
        'yu': u'ju',
        'vv': u'ə',
        'yo': u'jo',
        'uu': u'u',
        'wi': u'wi',
        'oo': u'o',
        'we': u'we',
        'wa': u'wa',
        'wv': u'wə',
        'xi': u'ɨi'
    }

    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []

    def __init__(self, input_dir, log=utils.logger.null_logger()):
        super(KCSSPreparator, self).__init__(input_dir, log=log)

        self.textgrid = self._load_textgrid()

        self.log.info('extracting segments...')
        self.segment = {}
        for utt, grid in self.textgrid.items():
            # extract from TextGrid file the tier that corresponds to
            # the utterance transcription. Use tiers[6] if orthographic
            # utterance transcription (instead of tiers[3]).
            for n, (tstart, tstop, _) in enumerate(grid.tiers[3].simple_transcript):
                utt_id = '{}-sent{}'.format(utt, str(n))
                self.segment[utt_id] = (utt, tstart, tstop)

    def _load_textgrid(self):
        """return the TextGrid files in a dict utt_id: textgrid data"""
        # build the list of all textgrid files to be parsed
        _dir = os.path.join(self.input_dir, 'label')
        _files = utils.list_files_with_extension(_dir, '.TextGrid', abspath=True)
        _name = {f: os.path.splitext(os.path.basename(f))[0] for f in _files}
        self.log.info('parsing %s TextGrid files...', len(_name))

        # auxiliary function for parsing a file. Register the files we
        # failed to parse
        _failed = []
        def _load(f):
            try:
                return TextGrid(codecs.open(f, 'r', encoding='utf16').read())
            except IndexError:
                _failed.append(f)

        # parse the files one per one
        bar = progressbar.ProgressBar(max_value=len(_files))
        textgrid = {}
        for i, f in enumerate(_files):
            l = _load(f)
            if l:
                textgrid[_name[f]] = l
            bar.update(i+1)

        # report any failed parse
        if _failed:
            self.log.error('failed to parse %s files', len(_failed))
            for f in _failed:
                self.log.debug('failed to parse %s', f)

        return textgrid

    def list_audio_files(self):
        wav_dir = os.path.join(self.input_dir, 'sounds')
        return utils.list_files_with_extension(wav_dir, '.wav', abspath=True)

    def make_segment(self):
        return self.segment

    def make_speaker(self):
        return {utt_id: utt_id[:3] for utt_id in self.segment.keys()}

    def _load_utterances(transcript, tutts):
        # sort by increasing tstart
        idx = 0
        for tstart, tstop in enumerate(sorted(tutts)):
            assert transcript[idx][0] == tstart


    def make_transcription(self):
        # first get the word level transcript for each textgrid file
        word_transcript = {k: v.tiers[2].simple_transcript
                           for k, v in self.textgrid.items()}

        # then go from word level to utt level using the segment times
        text = {}
        for utt_id, (_, tstart, tstop) in self.segment.items():
            utt_grid = utt_id.split('-sent')[0]
            words = word_transcript[utt_grid]

    def make_lexicon(self):
        pass

    def make_alignement_phones(self):
        pass

    def make_alignement_words(self):
        pass
