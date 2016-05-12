"""Abstract preparator for the GlobalPhone corpus"""
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
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.

import os
import re

import abkhazia.utils as utils
from abkhazia.prepare import AbstractPreparator


class AbstractGlobalPhonePreparator(AbstractPreparator):
    """Convert the GlobalPhone corpus to the abkhazia format"""

    name = 'globalphone'
    description = 'GlobalPhone multilingual read speech corpus'

    long_description = '''

    The GlobalPhone corpus developed in collaboration with the
    Karlsruhe Institute of Technology (KIT) was designed to provide
    read speech data for the development and evaluation of large
    continuous speech recognition systems in the most widespread
    languages of the world.

    In each language about 100 sentences were read from each of the
    100 speakers. The read articles cover national and international
    political news as well as economic news. The speech is available
    in 16bit, 16kHz mono quality. Speaker information like age,
    gender, occupation, etc. as well as information about the
    recording setup complement the database.'''

    url = [
        'Mandarin - http://catalog.elra.info/product_info.php?'
        'products_id=817&language=en',
        'Vietnamese - http://catalog.elra.info/product_info.php?'
        'products_id=1144&language=en']

    audio_format = 'shn'

    language = NotImplemented
    """the language for which the preparator is specilized for"""

    transcription_key = NotImplemented
    """the language dependant extention of transcription files"""

    exclude_wavs = []
    """a list (possibly empty) of wav files to ignore"""

    @staticmethod
    def strip_accolades(expr):
        """Returns 'expr' with accolade stripped, raise if no accolades"""
        if not (expr[0] == '{' and expr[-1] == '}'):
            raise RuntimeError(
                'Bad formatting for word or transcript: {0}'.format(expr))
        return expr[1:-1]

    def __init__(self, input_dir, log=utils.null_logger()):
        super(AbstractGlobalPhonePreparator, self).__init__(input_dir, log=log)

        self.transcription_dir = os.path.join(
            self.input_dir, 'GlobalPhone-{0}/{0}/{1}'
            .format(self.language, self.transcription_key))

        self.dictionary = os.path.join(
            self.input_dir,
            'GlobalPhoneDict-{}'.format(self.language),
            '{}-GPDict.txt'.format(self.language))

        # init language specificities
        self.wavs = None
        self._erase_dict = self.correct_dictionary()
        self._erase_trs = self.correct_transcription()

    def correct_transcription(self):
        return False

    def correct_dictionary(self):
        return False

    def __del__(self):
        try:
            # the corpus correction possibly create temporary files that
            # we delete here
            if self._erase_dict:
                utils.remove(self.dictionary)

            if self._erase_trs:
                utils.remove(self.transcription_dir)
        except AttributeError:
            pass

    def list_audio_files(self):
        # for some languages, there are corrupted wavefiles that we
        # need to exclude from preparation
        self.log.debug('%i audio files excluded', len(self.exclude_wavs))

        # src_dir is the 'adc' directory from the GlobalPhone
        # distribution of the language considered
        src_dir = os.path.join(
            self.input_dir, 'GlobalPhone-{0}/{0}/adc'.format(self.language))

        shns = [f for f in
                utils.list_files_with_extension(
                    src_dir, '.adc.shn', abspath=True, realpath=True)
                if os.path.basename(f).replace('.adc.shn', '')
                not in self.exclude_wavs]

        self.wavs = [os.path.basename(shn).replace('.adc.shn', '.wav')
                     for shn in shns]

        return zip(shns, self.wavs)

    def make_segment(self):
        segments = dict()
        for wav in self.wavs:
            wav = os.path.splitext(os.path.basename(wav))[0]
            segments[wav] = (wav, None, None)
        return segments

    def make_speaker(self):
        spk2utt = dict()
        for wav in self.wavs:
            wav = os.path.splitext(os.path.basename(wav))[0]
            spk2utt[wav] = wav[:5]
        return spk2utt

    def make_transcription(self):
        text = dict()
        for trs in utils.list_directory(self.transcription_dir, abspath=True):
            spk_id = os.path.splitext(os.path.basename(trs))[0]
            lines = utils.open_utf8(trs, 'r').readlines()

            # add utterence id from even lines starting at line 2
            ids = [spk_id + u'_' + re.sub(ur'\s+|:|;', u'', e)
                   for e in lines[1::2]]

            # delete linebreaks on odd lines starting at line 3
            # (this does not take into account fancy unicode
            # linebreaks), see
            # http://stackoverflow.com/questions/3219014
            transcriptions = [re.sub(ur'\r\n?|\n', u'', e)
                              for e in lines[2::2]]

            for i, trs in zip(ids, transcriptions):
                text[i] = trs
        return text

    def make_lexicon(self):
        # parse dictionary lines
        words, transcripts = [], []
        for line in utils.open_utf8(self.dictionary, 'r').readlines():
            # suppress linebreaks (this does not take into account fancy
            # unicode linebreaks), see
            # http://stackoverflow.com/questions/3219014
            line = re.sub(u'\r\n?|\n', u'', line).split(u' ')

            # parse word
            word = self.strip_accolades(line[0])
            if u'{' in word or u'}' in word:
                raise RuntimeError(
                    'Bad formatting of word {}'.format(word))
            words.append(word)

            # parse phonetic transcription
            trs = self.strip_accolades(u' '.join(line[1:])).split(u' ')
            transcript = []
            for phone in trs:
                if phone[0] == u'{':
                    phn = phone[1:]
                    assert phn != u'WB', trs
                elif phone[-1] == u'}':
                    phn = phone[:-1]
                    assert phn == u'WB', trs
                else:
                    phn = phone
                    assert phn != u'WB', trs

                assert not(u'{' in phn), trs
                assert not(u'}' in phn), trs
                if phn != u'WB':
                    transcript.append(phn)
            transcripts.append(u' '.join(transcript))

        return dict(zip(words, transcripts))
