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

"""Data preparation for the revised CSJ corpus"""

# MoraId == number or x or φ ??
# TagUncertainEnd=1
# TagUncertainStart=1
# <Noise
# <NonLinguisticSound
# LUWDictionaryForm=xxx(+)
#
# Alignment of various levels (sentences and phones)
# For 8 files: bad portions ???
#
# get info about speakers (M/F) into utt2spk and change name of files
# for more consistency
#
# what about non-core files?
#
# - keep FV and VN separate ? (fricative and voicing ?)
# - some empty sentences because they contain NonLinguisticSound
#   instead of SUW balise, treat these differently ?
# - isolated H sentences ?? maybe because some long vowel are spread
#   across two SUW for some reason ?  need to listen to it. If it is the
#   case, in preprocessing regroup these SUW.
#
# TODO remove redundancy from utt_ids (spk_id present twice ...)

import os
from collections import namedtuple
from pkg_resources import Requirement, resource_filename
import progressbar

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from abkhazia.utils import open_utf8
from abkhazia.utils.basic_io import cpp_sort
from abkhazia.prepare import AbstractPreparator

# from https://stackoverflow.com/questions/38987
def merge_two_dicts(first, second):
    '''Given two dicts, merge them into a new dict as a shallow copy'''
    third = first.copy()
    third.update(second)
    return third


Phone = namedtuple('Phone', 'id type start end')
Phoneme = namedtuple('Phone', 'id phones start end')
Word = namedtuple('Word', 'phonemes start end')
Utt = namedtuple('Utt', 'words start end channel')


# TODO group allophonic variants according to phonetics, is there really
# non-allophonic ones? Not if we consider 'y' as a phone
#
# Q -> long obstruents
# other q's -> glottal stops ?
# NH -> N
# other H -> long vowels
class CSJPreparator(AbstractPreparator):
    """convert the CSJ corpus to the abkhazia format"""
    name = 'csj'
    description = 'Corpus of Spontaneous Japanese'

    long_description = '''
    The Corpus of Spontaneous Japanese (CSJ) is a database of spoken
    Japanese. It contains 658 hours of speech consisting of
    approximately 7.5 million words. The speech materials were
    provided by more than 1,400 speakers of ages ranging from twenties
    to eighties.

    The CSJ has been publicly available since the spring of 2004. For
    more information, please visit the English web page of the
    Institute at: /corpus_center/csj/misc/preliminary/index_e.html'''

    url = 'http://www.ninjal.ac.jp/english/products/csj'
    audio_format = 'wav'

    vowels = {
        'a': u'ä',
        'e': u'e',
        'i': u'i',
        'o': u'o',
        'u': u'ɯ',  # this one has lip-compression
        'a:': u'ä:',
        'e:': u'e:',
        'i:': u'i:',
        'o:': u'o:',
        'u:': u'ɯ:'
    }

    # geminates: look at the effectives
    consonants = {
        'F': u'ɸ',    # not sure about this one
        'F:': u'ɸ:',  # not sure about this one
        'N': u'ɴ',    # maybe we should transcribe the N like the Q
                      # based on following consonant?
        'Q': u'ʔ',
        'b': u'b',
        'b:': u'b:',  # is this really a geminate with a voiced stop ?
        'd': u'd',
        'd:': u'd:',  # is this really a geminate with a voiced stop ?
        'g': u'g',
        'g:': u'g:',  # is this really a geminate with a voiced stop ?
        # look at difference between aspiration and gemination: gemination
        # is supposed to affect the duration of closure and aspiration the
        # VOT. This explains that gemination cannot occur at the beginning
        # of an utterance no way to determine the duration of closure
        'h': u'h',
        'k': u'k',
        'k:': u'k:',
        'm': u'm',
        'n': u'n',
        'p': u'p',
        'p:': u'p:',
        'r': u'r',
        's': u's',
        's:': u's:',
        'sy': u'ɕ',
        'sy:': u'ɕ:',
        't': u't',
        't:': u't:',
        'w': u'w',  # lip-compression here too...
        'y': u'j',
        'z': u'z',
        'zy': u'ʑ',  # very commonly an affricate...
        'zy:': u'ʑ:'
    }

    # phones are vowels and consonents
    phones = merge_two_dicts(vowels, consonants)

    silences = ['SPN', 'NSN']

    variants = []

    def __init__(self, input_dir, output_dir=None,
                 verbose=False, njobs=1, copy_wavs=False):
        # call the AbstractPreparator __init__
        super(CSJPreparator, self).__init__(
            input_dir, output_dir, verbose, njobs)

        self.copy_wavs = copy_wavs

        # load the core_CSJ.txt from the abkhazia installation path
        core = resource_filename(
            Requirement.parse('abkhazia'), 'abkhazia/share/CSJ_core.txt')
        if not os.path.exists(core):
            raise OSError('core_CSJ not found in {}'.format(core))
        core_files = [l[:-1] for l in open(core, 'r').readlines()]

        # select laymen talks only, from core part of the corpus
        xml_dir = os.path.join(self.input_dir, 'XML')
        self.data_files = os.listdir(xml_dir)
        self.data_files = [f.replace('.xml', '') for f in self.data_files]
        self.data_files = [f for f in self.data_files
                           if f[0] == 'S' and f in core_files]

        # gather label data TODO parallelize
        self.log.info('parsing {} xml files...'.format(len(self.data_files)))
        self.all_utts = {}
        self.lexicon = {}
        for data in progressbar.ProgressBar()(self.data_files):
            utts = self.parse_core_xml(os.path.join(xml_dir, data + '.xml'))
            utts, utt_lexicon = self.extract_basic_transcript(utts)

            for utt_id in utts:
                assert not(utt_id in self.all_utts), utt_id
                self.all_utts[utt_id] = utts[utt_id]

            for word in utt_lexicon:
                if word not in self.lexicon:
                    self.lexicon[word] = utt_lexicon[word]

        # TODO was present in Thomas's script but not used
        # all_phones = set([phone for transcript in self.lexicon.values()
        #                   for phone in transcript])

    def parse_core_xml(self, xml_file):
        """Parse raw transcript"""
        tree = ET.ElementTree(file=xml_file)
        talk = tree.getroot()
        talk_id = talk.attrib["TalkID"]
        speaker = talk.attrib["SpeakerID"]

        # make sure all speaker-ids have same length
        if len(speaker) < 4:
            speaker = "0"*(4-len(speaker)) + speaker
        else:
            assert len(speaker) == 4, talk_id

        # using kanji for 'male'
        gender = 'M' if talk.attrib["SpeakerSex"] == u"男" else 'F'
        spk_id = gender + speaker

        if talk_id[0] == "D":
            is_dialog = True
        else:
            is_dialog = False

        # Utterance level
        utts = {}
        for ipu in talk.iter("IPU"):
            utt_id = spk_id + u"_" + talk_id + u"_" + ipu.attrib["IPUID"]
            channel = ipu.attrib["Channel"] if is_dialog else None
            utt_start = float(ipu.attrib["IPUStartTime"])
            utt_stop = float(ipu.attrib["IPUEndTime"])

            # Word level - Short Words Units (SUW) are taken as 'words'
            words = []
            for suw in ipu.iter("SUW"):
                # Phoneme level
                phonemes = []
                for phoneme in suw.iter("Phoneme"):
                    phoneme_id = phoneme.attrib["PhonemeEntity"]
                    # Phone level (detailed phonetic)
                    phones = []
                    for phone in phoneme.iter("Phone"):
                        start = float(phone.attrib["PhoneStartTime"])
                        stop = float(phone.attrib["PhoneEndTime"])
                        id = phone.attrib["PhoneEntity"]
                        phn_class = phone.attrib["PhoneClass"]
                        phones.append(Phone(id, phn_class, start, stop))
                    if phones:
                        phonemes.append(Phoneme(
                            phoneme_id, phones, phones[0].start, phones[-1].end))
                    else:
                        self.log.debug(utt_id)
                if phonemes:
                    words.append(Word(
                        phonemes, phonemes[0].start, phonemes[-1].end))
                else:
                    try:
                        moras = [mora.attrib["MoraEntity"]
                                 for mora in suw.iter("Mora")]
                        self.log.debug(moras)
                    except:
                        pass
                    self.log.debug(utt_id)
                    # FIXME understand this
                    # assert u"φ" in moras, utt_id
            utts[utt_id] = Utt(words, utt_start, utt_stop, channel)
        return utts


    def check_transcript_consistency(self, utts):
        pass
    # TODO check consistency of starts, stops, subsequent starts at all levels
    # and the across level consistency


    def extract_basic_transcript(self, utts, encoding=None):
        lexicon = {}
        new_utts = {}
        for utt_id in utts:
            utt = utts[utt_id]
            if not utt.words:
                self.log.debug('Empty utt: ' + utt_id)
            else:
                # TODO correct these before this step
                if utt.words[0].start < utt.start:
                    self.log.debug(
                        utt_id + ' start: ' +
                        str(utt.start) + ' - ' +
                        str(utt.words[0].start))
                if utt.words[-1].end > utt.end:
                    self.log.debug(
                        utt_id + ' end: ' +
                        str(utt.end) + ' - ' +
                        str(utt.words[-1].end))

                start = min(utt.words[0].start, utt.start)
                stop = max(utt.words[-1].end, utt.end)

                words = []
                for word in utt.words:
                    # use phonemic level
                    phonemes = self.reencode(
                        [phoneme.id for phoneme in word.phonemes], encoding)

                    #print('-'.join(phonemes))
                    #print('-'.join([phoneme.id for phoneme in word.phonemes]))
                    if phonemes == ['H']:  # just drop these for now
                        pass # TODO log this
                    else:
                        word = u"-".join(phonemes)
                        if word not in lexicon:
                            lexicon[word] = phonemes
                        words.append(word)
                new_utts[utt_id] = {'words': words, 'start': start, 'end': stop}
        return new_utts, lexicon


    def reencode(self, phonemes, encoding=None):
        vowels = ['a', 'e', 'i', 'o', 'u']
        stops = ['t', 'ty', 'b', 'by', 'g', 'gj', 'gy',
                 'k', 'ky', 'kj', 'p', 'py', 'd', 'dy']
        affricates = ['z', 'zy', 'zj', 'c', 'cy', 'cj']
        fricatives = ['s', 'sj', 'sy', 'z', 'zy', 'zj', 'h', 'F', 'hy', 'hj']
        obstruents = affricates + fricatives  + stops

        phonemes_1 = []
        for phoneme in phonemes:
            # 1 - Noise and rare phonemes
            out_phn = phoneme
            # getting rid of very rare phones as vocal noise
            if out_phn in ['kw', 'v', 'Fy']:
                out_phn = 'VN'
            # rewriting FV and VN (fricative voicing and vocal noise) as
            # SPN (spoken noise)
            if out_phn in ['FV', 'VN']:
                out_phn = 'SPN'
            # rewriting ? as NSN (generic noise)
            if out_phn == '?':
                out_phn = 'NSN'
            # 2 - breaking clusters
            seg_1 = {
                'ky': 'k',
                'ty': 't',
                'ry': 'r',
                'cy': 't',
                'cj': 't',
                'c': 't',
                'py': 'p',
                'ny': 'n',
                'by': 'b',
                'my': 'm',
                'hy': 'h',
                'gy': 'g',
                'dy': 'd'
            }
            seg_2 = {
                'ky': 'y',
                'ty': 'y',
                'ry': 'y',
                'cy': 'sy',
                'cj': 'sj',
                'c': 's',
                'py': 'y',
                'ny': 'y',
                'by': 'y',
                'my': 'y',
                'hy': 'y',
                'gy': 'y',
                'dy': 'y'
            }
            if out_phn in seg_1:
                out_phns = [seg_1[out_phn], seg_2[out_phn]]
            else:
                out_phns = [out_phn]
                # 3 - group allophonic variants according to phonetics
            mapping = {
                'zj': 'zy',
                'cj': 'cy',
                'sj': 'sy',
                'nj': 'n',
                'kj': 'k',
                'hj': 'h',
                'gj': 'g'
            }
            out_phns = [mapping[phn] if phn in mapping else phn for phn in out_phns]
            phonemes_1 = phonemes_1 + out_phns

        # 4 - Q before obstruent as geminate (long obstruent)
        if len(phonemes_1) <= 1:
            phonemes_2 = phonemes_1
        else:
            phonemes_2 = []
            previous = phonemes_1[0]

            for phoneme in phonemes_1[1:]:
                out_phn = phoneme
                if previous == 'Q':
                    assert out_phn != 'Q', "Two successive 'Q' in phoneme sequence"
                    if out_phn in obstruents:
                        previous = out_phn + ':'
                    else:
                        # Q considered a glottal stop in other contexts
                        phonemes_2.append('Q')
                        previous = out_phn
                else:
                    phonemes_2.append(previous)
                    previous = out_phn
            phonemes_2.append(previous)  # don't forget last item

        # 5 - H after vowel as long vowel
        if len(phonemes_2) <= 1:
            if 'H' in phonemes_2:
                self.log.debug("Isolated H: " + str(phonemes) + str(phonemes_1))
            phonemes_3 = phonemes_2
        else:
            phonemes_3 = []
            previous = phonemes_2[0]
            assert not(previous == 'H'), "Word starts with H"
            for phoneme in phonemes_2[1:]:
                out_phn = phoneme
                if out_phn == 'H':
                    assert previous != 'H', "Two successive 'H' in phoneme sequence"
                    if previous in vowels:
                        phonemes_3.append(previous + ':')
                    else:
                        assert previous == 'N', "H found after neither N nor vowel"
                        phonemes_3.append(previous)  # drop H after N
                    previous = 'H'
                else:
                    if previous != 'H':
                        phonemes_3.append(previous)
                    previous = out_phn
            if previous != 'H':
                phonemes_3.append(previous)  # don't forget last item
        return phonemes_3


    def list_audio_files(self):
        inputs = [os.path.join(self.input_dir, 'Waveforms', data + '.wav')
                  for data in self.data_files]
        outputs = [os.path.join(data + '.wav') for data in self.data_files]
        return inputs, outputs


    def make_segment(self):
        with open_utf8(self.segments_file, 'w') as out:
            for utt_id in self.all_utts:
                wavefile = utt_id.split("_")[1] + ".wav"
                start = self.all_utts[utt_id]['start']
                stop = self.all_utts[utt_id]['end']
                out.write(u"{0} {1} {2} {3}\n"
                          .format(utt_id, wavefile, start, stop))
        cpp_sort(self.segments_file)


    def make_speaker(self):
        with open_utf8(self.speaker_file, 'w') as out:
            for utt_id in self.all_utts:
                spk_id = utt_id.split("_")[0]
                out.write(u"{0} {1}\n".format(utt_id, spk_id))
        cpp_sort(self.speaker_file)


    def make_transcription(self):
        with open_utf8(self.transcription_file, 'w') as out:
            for utt_id in self.all_utts:
                words = u" ".join(self.all_utts[utt_id]['words'])
                out.write(u"{0} {1}\n".format(utt_id, words))
        cpp_sort(self.transcription_file)


    def make_lexicon(self):
        with open_utf8(self.lexicon_file, 'w') as out:
            for word in self.lexicon:
                transcript = u" ".join(self.lexicon[word])
                out.write(u"{0} {1}\n".format(word, transcript))
        cpp_sort(self.lexicon_file)
