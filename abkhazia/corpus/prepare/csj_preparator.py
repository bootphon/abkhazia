# coding: utf-8
# Copyright 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
import sys
from collections import namedtuple
from pkg_resources import Requirement, resource_filename
import progressbar

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparator
from abkhazia.utils import open_utf8

reload(sys)

sys.setdefaultencoding('utf8')

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
    approximately 7.5 million words from more than 1,400 speakers.
    It is publicly available at
    /corpus_center/csj/misc/preliminary/index_e.html
    '''

    url = 'http://www.ninjal.ac.jp/english/products/csj'
    audio_format = 'wav'
    vowels = {
        'a': u'ä',
        'e': u'e',
        'i': u'i',
        'o': u'o',
        'u': u'ɯ',  # this one has lip-compression
        'a+H': u'ä+H',
        'e+H': u'e+H',
        'i+H': u'i+H',
        'o+H': u'o+H',
        'u+H': u'ɯ+H',
        'TN': u'TN'
    }

    # geminates: look at the effectives
    consonants = {
        'F': u'ɸ',    # not sure about this one
        'F:': u'ɸ:',  # not sure about this one
        'Q+F': u'Q+F',
        'N': u'ɴ',    # maybe we should transcribe the N like the Q
                      # based on following consonant?
        'Q': u'ʔ',
        'b': u'b',
        'b:': u'b:',  # is this really a geminate with a voiced stop ?
        'd': u'd',
        'd:': u'd:',  # is this really a geminate with a voiced stop ?
        'Q+d': u'Q+d',
        'g': u'g',
        'g:': u'g:',  # is this really a geminate with a voiced stop ?
        'Q+g': u'Q+g',
        # look at difference between aspiration and gemination: gemination
        # is supposed to affect the duration of closure and aspiration the
        # VOT. This explains that gemination cannot occur at the beginning
        # of an utterance no way to determine the duration of closure
        'h': u'h',
        'h:': u'h:',  # TODO ASK THOMAS IF I SHOULD PUT IT ?
        'Q+h': u'Q+h',
        'k': u'k',
        'k:': u'k:',
        'Q+k': u'Q+k',
        'm': u'm',
        'n': u'n',
        'p': u'p',
        'p:': u'p:',
        'Q+p': u'Q+p',
        # TODO ASK THOMAS AND XUAN-NGA !! 
        'py:': u'py:',
        'Q+py': u'Q+py',
        'cy:': u'cy:',
        'Q+cy': u'Q+cy',
        'dy': u'dy',
        'gy': u'gy',
        'cy': u'cy',
        'hy': u'hy',
        'py': u'py',
        'ry': u'ry',
        'ny': u'ny',
        'by': u'by',
        'c': u'c',
        'c:': u'c:',
        'Q+c': u'Q+c',
        'ky': u'ky',
        'ky:': u'ky:',
        'Q+ky': u'Q+ky',
        'my': u'my',
        # TODO ASK THOMAS AND XUAN-NGA
        'r': u'r',
        's': u's',
        's:': u's:',
        'Q+s': u'Q+s',
        'sy': u'ɕ',
        'sy:': u'ɕ:',
        'Q+sy': u'Q+sy',
        't': u't',
        't:': u't:',
        'Q+t': u'Q+t',
        'w': u'w',  # lip-compression here too...
        'y': u'j',
        'z': u'z',
        'z:': u'z:',  # TODO ASK THOMAS IF IS SHOULD PUT IT ?
        'Q+z': u'Q+z',
        'zy': u'ʑ',  # very commonly an affricate...
        'zy:': u'ʑ:',
        'Q+zy': u'Q+zy'
    }   

    
    # XML with bad transcription:
    xml_pb = 'S05M1406.xml'

    # phones are vowels and consonents
    phones = utils.merge_dicts(vowels, consonants)

    silences = ['SPN', 'NSN']

    variants = []

    def __init__(self, input_dir,  log=utils.logger.null_logger(),
                 copy_wavs=False, clusters=False, treat_core=False):
        super(CSJPreparator, self).__init__(input_dir, log)
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
        self.non_core_files = [f for f in self.data_files
                               if f[0] == 'S' and f not in core_files]
        self.data_core_files = [f for f in self.data_files
                                if f[0] == 'S' and f in core_files]
        self.data_files = [f for f in self.data_files
                           if f[0] == 'S']

        self.kana_to_phone = self.parse_kana_to_phone(
                resource_filename(Requirement.parse('abkhazia'),
                    'abkhazia/share/kana-to-phone_bootphon_CSJ.txt'))

        # gather label data TODO parallelize
        self.log.info('parsing {} xml files'.format(len(self.data_files)))
        self.all_utts = {}
        self.lexicon = {}

        if treat_core:
            self.data_files = self.data_core_files

        for data in progressbar.ProgressBar()(self.data_files[1040:]):
            print "xml :", data
            if treat_core:
                utts = self.parse_core_xml(
                        os.path.join(xml_dir, data + '.xml'))
            else:
                #if not data == 'S05F0612':
                #    continue
                #else : 
                #    print data
                utts = self.parse_non_core_xml(
                    os.path.join(xml_dir,data + '.xml'), clusters)
                for utt_id in utts:
                    utt = utts[utt_id]
            utts, utt_lexicon = self.extract_basic_transcript(utts,
                                                              clusters)
            for utt_id in utts:
                assert not(utt_id in self.all_utts), utt_id
                self.all_utts[utt_id] = utts[utt_id]

            for word in utt_lexicon:
                if word not in self.lexicon:
                    if word=='-' : 
                        continue
                    self.lexicon[word] = utt_lexicon[word]

    def parse_kana_to_phone(self,kana_csv):
        """Parse katakana phone transcription and pu it in a dict() """ 
        kana_to_phon = dict()
        with open_utf8(kana_csv, 'r') as fin:
            kana_transcript = fin.read()
            kana_transcript = kana_transcript.split('\n')
            for line in kana_transcript[1:]:
                if line == '':
                    continue
                phones = line.split('\t')
                katakana = phones[0].decode('utf8')
                bootphon = phones[3]
                if bootphon == '':
                    bootphon == "H"
                kana_to_phon[katakana] = bootphon
        return(kana_to_phon)

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
                    # else:
                    #     self.log.debug(utt_id)
                if phonemes:
                    words.append(Word(
                        phonemes, phonemes[0].start, phonemes[-1].end))
                else:
                    try:
                        moras = [mora.attrib["MoraEntity"]
                                 for mora in suw.iter("Mora")]
                        # self.log.debug(moras)
                    except:
                        pass
                    # self.log.debug(utt_id)
                    # FIXME understand this
                    # assert u"φ" in moras, utt_id
            utts[utt_id] = Utt(words, utt_start, utt_stop, channel)
        return utts

    def parse_non_core_xml(self, xml_file, keep_clusters):
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
            #if not ipu.attrib["IPUID"]=='0178':
            #    continue
            utt_id = spk_id + u"_" + talk_id + u"_" + ipu.attrib["IPUID"]
            channel = ipu.attrib["Channel"] if is_dialog else None
            utt_start = float(ipu.attrib["IPUStartTime"])
            utt_stop = float(ipu.attrib["IPUEndTime"])
            # Word level - Short Words Units (SUW) are taken as 'words'
            words = []
            for luw in ipu.iter("LUW"):
                phonemes=[]
                for suw in luw.iter("SUW"):
                    # Phoneme level
                    #phonemes = []
                    phones = suw.attrib["PhoneticTranscription"]
                    phones.encode('utf8')
                    whole_phone = phones

                    # in X05M1406.xml, transcription starts a word with H : replace by "?"
                    xml_name = xml_file.split('/')[-1]
                    if xml_name == self.xml_pb and phones =='ーノ':
                        phones = '?'
                    # TODO check why causes problem ? supposed to be N H 
                    if  'ンー' in phones : 
                        phones = '?'
                        
                    # If phonetic transcription has a "W" or "B"  it means
                    # theres a difference between what is spoken and real word
                    # so choose what is spoken (i.e. in "(W XX ; YY) choose XX)
                    #if "W" in phones or "B" in phones:
                    #while ("W" in phones and ";" in phones) or ("B" in phones and ";" in phones) :
                    #    split_phones=phones.split(';')
                    #    real_phones=split_phones[0].replace('(W ','')
                    #    for parts in split_phones[1:]: 
                    #        # locate the end of the "W/B" ambiguity
                    #        # and get the end of the phoneme if there's 
                    #        # something after the "(W ..;..).." 
                    #        try:
                    #            ind=parts.index(')')
                    #        except:
                    #            # there's cases where they forgot the end ")"
                    #            ind=len(parts)-1

                    #            real_phones=real_phones+parts[ind+1:]
                    #        phones=real_phones
                    if "W" in phones or "?" in phones or "B" in phones or "O" in phones : 
                        phone = []
                        phone.append(Phone(
                                    "TN", '', None, None))
                        phonemes.append(Phoneme(
                                    "TN", phone, phone[0].start, phone[-1].end))
                        continue

                    # P indicated a pause and is followed by 20 and ":" 
                    # numbers, exlude everything
                    while "P" in phones :
                        ind = phones.index('P')
                        phones = phones[0:ind]+phones[ind+21:]

                    # Remove the transcription tags and other 
                    # unwanted characters (e.g. ',' '-' etc..)
                    word_tags = ['A', 'B', 'M', 'I',
                                 'S', 'J', 'C', 'L',
                                 'R', 'G', 'F', 'D',
                                 'H', 'Q', 'R', 'O',
                                 'V', 'W', '息', '笑',
                                 '咳','泣'
                                ]
                    symbols = [',', '-', '>', '<', '(', ')', ' ', '×', '.', ':']
                    additional_tags = ['1', '2', '3', '4',
                                       '5', '6', '7', '8', 
                                       '9', '0']
                    unwanted = word_tags + symbols + additional_tags

                    for tag in unwanted:
                        if tag in phones:
                            phones=phones.replace(tag, '')

                    # use mapping of every symbol in transcription  
                    while len(phones)>0:
                        phone = []
                        phoneme_id1 = None
                        phoneme_id2 = None 
                        # First check if first two symbols are together
                        if len(phones[0:2])>1 and phones[0:2] in self.kana_to_phone:
                            phoneme_id = self.kana_to_phone[phones[0:2]]
                            phones=phones[2:]
                        
                        elif phones[0] in self.kana_to_phone : 
                            # Else check if the symbol is in kana to phon
                            phoneme_id = self.kana_to_phone[phones[0]]
                            phones=phones[1:]
                        
                        else :
                            # If not, let it pass, it will be treated later on    
                            phoneme_id = phones[0]
                            if phoneme_id == "?" :
                                phones=phones[1:]
                                continue
                            print "Phone seems to have no mapping, check :", phoneme_id, ' in context :', whole_phone
                            raw_input()
                            phones=phones[1:]
                                        
                        ## handle the x+H case
                        #if ('+' in phoneme_id) and phoneme_id[-1]=='H':
                        #    plus_ind = phoneme_id.index('+')
                        #    phoneme_id = phoneme_id[0:plus_ind] + 'H'
                        if (('+' in phoneme_id) and (not keep_clusters) and
                            not (phoneme_id[-1] == 'H')):
                            # handle the x+x x case
                            plus_ind = phoneme_id.index('+')
                            phoneme_id2 = phoneme_id[plus_ind+2]
                            phoneme_id1 = phoneme_id[0:plus_ind] + phoneme_id[plus_ind+1]
                            
                            #phoneme_id=None
                        elif (('+' in phoneme_id) and (keep_clusters) and
                                not (phoneme_id[-1] == 'H')):
                            # if keep_clusters is enabled, keep the x+x
                            # (e.g. c+y) as is
                            try:
                                phoneme_id2 = phoneme_id[3]
                                phoneme_id1 = phoneme_id[0:3]
                            except:
                                phoneme_id = phoneme_id[0:3]
                                pass
                        
                        if phoneme_id == "Q":
                            # If Q is at the end, remove it !
                            if len(phones) == 0:
                                phoneme_id = None
                                continue
                        
                        if phoneme_id == 'Nfiller':
                            # TODO CHECK IF Nfiller is N
                            phoneme_id = 'N'
                        
                        if phoneme_id2:
                            phone.append(Phone(
                                phoneme_id1, '', None, None))
                            phonemes.append(Phoneme(
                                phoneme_id1, phone, phone[0].start, phone[-1].end))

                            phone.append(Phone(
                                phoneme_id2, '', None, None))
                            phonemes.append(Phoneme(
                                phoneme_id2, phone, phone[0].start, phone[-1].end))
                            continue
                        else:
                            if '+' not in phoneme_id:
                                for char in phoneme_id:
                                    phone.append(Phone(
                                        char, '', None, None))
                                    phonemes.append(Phoneme(
                                        char, phone, phone[0].start, phone[-1].end))
                            else:
                                phone.append(Phone(
                                    phoneme_id, '', None, None))
                                phonemes.append(Phoneme(
                                    phoneme_id, phone, phone[0].start, phone[-1].end))
                
                if phonemes:
                    words.append(Word(
                        phonemes, phonemes[0].start, phonemes[-1].end))
            else:
                try:
                    moras = [mora.attrib["MoraEntity"]
                             for mora in suw.iter("Mora")]
                    # self.log.debug(moras)
                except:
                    pass
                # self.log.debug(utt_id)
                # FIXME understand this
                # assert u"φ" in moras, utt_id
            utts[utt_id] = Utt(words, utt_start, utt_stop, channel)
        return utts

    def check_transcript_consistency(self, utts):
        pass
    # TODO check consistency of starts, stops, subsequent starts at all levels
    # and the across level consistency

    def extract_basic_transcript(self, utts, encoding=None, clusters=False):
        lexicon = {}
        new_utts = {}
        for utt_id in utts:
            utt = utts[utt_id]
            # if not utt.words:
            #     self.log.debug('Empty utt: ' + utt_id)
            # else:
            if utt.words:
                # TODO correct these before this step
                # if utt.words[0].start < utt.start:
                #     self.log.debug(
                #         utt_id + ' start: ' +
                #         str(utt.start) + ' - ' +
                #         str(utt.words[0].start))
                # if utt.words[-1].end > utt.end:
                #     self.log.debug(
                #         utt_id + ' end: ' +
                #         str(utt.end) + ' - ' +
                #         str(utt.words[-1].end))

                #start = min(utt.words[0].start, utt.start)
                #stop = max(utt.words[-1].end, utt.end)
                start = utt.start
                stop = utt.end

                words = []
                for word in utt.words:
                    # use phonemic level
                    
                    phonemes = self.reencode(
                        [phoneme.id for phoneme in word.phonemes],
                        clusters, encoding)

                    ###print('-'.join(phonemes))
                    ###print('-'.join([phoneme.id for phoneme in word.phonemes]))
                    if phonemes == ['H']:  # just drop these for now
                        pass # TODO log this
                    else:
            ##print phonemes
            #if phonemes=='':
                #print 'empty phoneme !!'
                        word = u"-".join(phonemes)
                        if word not in lexicon:
                            lexicon[word] = phonemes
                        words.append(word)
                new_utts[utt_id] = {'words': words, 'start': start, 'end': stop}
        return new_utts, lexicon

    def reencode(self, phonemes, encoding=None, clusters=False):
        vowels = ['a', 'e', 'i', 'o', 'u','TN']
        stops = ['t', 'ty', 'b', 'by', 'g', 'gj', 'gy',
                 'k', 'ky', 'kj', 'p', 'py', 'd', 'dy']
        affricates = ['z', 'zy', 'zj', 'c', 'cy', 'cj']
        fricatives = ['s', 'sj', 'sy', 'z', 'zy', 'zj', 'h', 'F', 'hy', 'hj']
        obstruents = affricates + fricatives + stops
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
            if out_phn in seg_1 and not clusters:
                out_phns = [seg_1[out_phn], seg_2[out_phn]]
            #elif "+" in out_phn and clusters:
            #    out_phns = [out_phn[0]+out_phn[2]]
            #    if out_phn not in self.phones:
            #        self.phones[out_phn] = out_phn
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
                #print phoneme,' in ',phonemes_1
                        assert out_phn != 'Q', "Two successive 'Q' in phoneme sequence"
                        if out_phn in obstruents:
                            previous = 'Q'+out_phn
                        else:
                            # Q considered a glottal stop in other contexts
                            phonemes_2.append('Q')
                            previous = out_phn
                    else:
                        phonemes_2.append(previous)
                        previous = out_phn
                phonemes_2.append(previous)  # don't forget last item
            # 5 - H after vowel as long vowel
            if len(phonemes_2) <= 1 :
                # if 'H' in phonemes_2:
                #     self.log.debug("Isolated H: " + str(phonemes) + str(phonemes_1))
                phonemes_3 = phonemes_2
            elif (phonemes_2[0]=='H' and len(phonemes_2)==2):
                print "Word starts with H : erasing H"
                phonemes_2 = phonemes_2[1:]
                phonemes_3 = phonemes_2
            else:
                phonemes_3 = []
                previous = phonemes_2[0]
                #assert not(previous == 'H'), "Word starts with H"
                if previous == 'H':
                    print "Word starts with H : erasing H"
                    phonemes_2 = phonemes_2[1:]
                for phoneme in phonemes_2[1:]:
                    out_phn = phoneme
                    if out_phn == 'H':
                        assert previous != 'H', "Two successive 'H' in phoneme sequence"
                        if previous in vowels:
                            phonemes_3.append(previous + ':')
                        else:
                            print previous
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
        return [os.path.join(self.input_dir, 'Waveforms', data + '.wav')
                for data in self.data_files]

    def make_segment(self):
        segments = dict()
        for utt_id in self.all_utts:
            wavefile = utt_id.split("_")[1]
            start = self.all_utts[utt_id]['start']
            stop = self.all_utts[utt_id]['end']
            segments[utt_id] = (wavefile, float(start), float(stop))
        return segments

    def make_speaker(self):
        utt2spk = dict()
        for utt_id in self.all_utts:
            utt2spk[utt_id] = utt_id.split("_")[0]
        return utt2spk

    def make_transcription(self):
        text = dict()
        for utt_id in self.all_utts:
            words = u" ".join(self.all_utts[utt_id]['words'])
            text[utt_id] = words
        return text

    def make_lexicon(self):
        return {k: ' '.join(v) for k, v in self.lexicon.iteritems()}
