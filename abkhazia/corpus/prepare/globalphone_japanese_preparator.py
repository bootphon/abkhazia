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

"""Japanese specific preprocessing for the GlobalPhone corpus

"""

import tempfile
import os
import abkhazia.utils as utils

from abkhazia.utils import open_utf8
from abkhazia.corpus.prepare.globalphone_abstract_preparator import (
    AbstractGlobalPhonePreparator)


class JapanesePreparator(AbstractGlobalPhonePreparator):
    """Japanese specific preprocessing for the GlobalPhone corpus"""
    language = 'Japanese'

    name = '-'.join([AbstractGlobalPhonePreparator.name, language]).lower()

    transcription_key = 'rmn'
    missing_transcripts = [
        'JA223_92','JA223_93','JA223_94','JA223_95',
        'JA223_96','JA223_97','JA223_98','JA223_99',
        'JA223_100','JA223_101','JA223_102','JA223_103',
        ]

    exclude_wavs =  missing_transcripts

    #vowels = {
    #    'a': u'ä',
    #    'e': u'e',
    #    'i': u'i',
    #    'o': u'o',
    #    'u': u'ɯ',  # this one has lip-compression
    #    'a:': u'ä:',
    #    'e:': u'e:',
    #    'i:': u'i:',
    #    'o:': u'o:',
    #    'u:': u'ɯ:',
    #    'NSN': u'NSN'
    #}
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
        'u+H': u'ɯ+H'
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
    # source for IPA notation:
    # https://en.wikipedia.org/wiki/Tone_%28linguistics%29#Phonetic_notation
    #tones = [
    #    ('1', u'˥'),
    #    ('2', u'˧˥'),
    #    ('3', u'˨˩˦'),
    #    ('4', u'˥˩'),
    #    ('5', u'˧')  # mid-level neutral
    #]

    #four_tones_vowels = ['va', 've', 'iou']

    # generate dict associating phones with ipa and tonal variants
    variants = []
    phones = utils.merge_dicts(vowels,consonants)
    #for vowel, ipa in vowels.iteritems():
    #    l_tones = tones[:-1] if vowel in four_tones_vowels else tones
    #    for tone, ipa_t in l_tones:
    #        tonal = vowel + tone
    #        assert tonal not in phones
    #        phones[tonal] = ipa + ipa_t

    #    variants.append([vowel + tone for tone, _ in l_tones])
    
    
    def parse_kana_to_phone(self):
        """Parse katakana phone transcription and pu it in a dict() """ 
        kana_to_phon=dict()
        kana_csv=os.path.join(self.input_dir,'kana-to-phon_bootphon.txt')
        with open_utf8(kana_csv,'r') as fin:
            kana_transcript = fin.read()
            kana_transcript = kana_transcript.split('\n')
            for line in kana_transcript[1:]:
                if line =='':
                    continue
                phones=line.split('\t')
                GP_phone=phones[1].decode('utf8')
                bootphon=phones[2]
                kana_to_phon[GP_phone]=bootphon
        return(kana_to_phon)

    def transcript_japanese(self, trs, clusters):
        """ Go from GP japanese symbol to bootphon symbols.
        For each phone, check first if current phone +
        next phone are in kana_to_phone, if not, check 
        only current phone.
        """
        transcript=[]
        not_in_kana=[]
        for ind,phone in enumerate(trs):
            if phone=="WB}":
                del trs[ind]
            if not trs:
                break
        for ind,phone in enumerate(trs):
            phn = self.strip_phone(phone)
            #if ind<len(trs)-2:
            #    # first check the three phones
            #    third_phone = trs[ind+2]
            #    third_phn = self.strip_phone(third_phone)

            #    next_phone = trs[ind+1]
            #    next_phn = self.strip_phone(next_phone)
        
            #    three_phn = ' '.join([phn,next_phn,third_phn])
            #    both_phn = ' '.join([phn,next_phn])
            #    if three_phn in self.kana_to_phone :
            #        phn = three_phn
            #    if both_phn in self.kana_to_phone : 
            #        #if three phones not in file
            #        # check if two phones are
            #        phn = both_phn

            #elif ind<len(trs)-1:
            #    #check two phones 
            #    next_phone = trs[ind+1]
            #    next_phn = self.strip_phone(next_phone)
        
            #    both_phn = ' '.join([phn,next_phn])
            #    if both_phn in self.kana_to_phone : 
            #        phn = both_phn

            if phn in self.kana_to_phone:
                out_phn = self.kana_to_phone[phn]

                if out_phn =='Nfiller':
                    out_phn='N'
                for char in out_phn:
                    if not (char=='+'):
                        transcript.append(char)
            elif phn=="SIL":
                transcript.append(phn)
            else:
                print "phn is:",phn,": and phn in kana :", phn in self.kana_to_phone
                if not phn == "WB" :
                    if ind>1:
                        prev_phn=self.strip_phone(trs[ind-1])
                    else : 
                        prev_phn=None
                    if ind<len(trs)-1:
                        next_phn=self.strip_phone(trs[ind+1])
                    else : 
                        next_phn=None

                    not_in_kana.append((phn,prev_phn,next_phn))
                transcript.append('?')
        final_transcript=self.reencode(transcript,clusters)
        return(final_transcript,not_in_kana)
        
    def strip_phone(self,phone):
        """ remove accolades from phone"""
        if phone[0] == u'{':
            phn = phone[1:]
            assert phn != u'WB', phone
        elif phone[-1] == u'}' :
            phn = phone[:-1]
            assert phn == u'WB', phone
        else:
            phn = phone
            assert phn != u'WB', phone
        phn.replace(' ','')
        return(phn)

    def reencode(self, phonemes, encoding=None, clusters=False):
        print clusters
        vowels = ['a', 'e', 'i', 'o', 'u']
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
                out_phn = ''
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
            elif "+" in out_phn and clusters:
                out_phns = [out_phn[0]+out_phn[2]]
                #if out_phn not in self.phones:
                #    self.phones[out_phn] = out_phn
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
                        previous = 'Q+' + out_phn 
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
            # if 'H' in phonemes_2:
            #     self.log.debug("Isolated H: " + str(phonemes) + str(phonemes_1))
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
                        phonemes_3.append(previous + '+H')
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

    #def reencode(self, phonemes, encoding=None):
    #    vowels = ['a', 'e', 'i', 'o', 'u']
    #    stops = ['t', 'ty', 'b', 'by', 'g', 'gj', 'gy',
    #             'k', 'ky', 'kj', 'p', 'py', 'd', 'dy']
    #    affricates = ['z', 'zy', 'zj', 'c', 'cy', 'cj']
    #    fricatives = ['s', 'sj', 'sy', 'z', 'zy', 'zj', 'h', 'F', 'hy', 'hj']
    #    obstruents = affricates + fricatives + stops
    #    phonemes_1 = []
    #    for phoneme in phonemes:
    #        # 1 - Noise and rare phonemes
    #        out_phn = phoneme
    #        # getting rid of very rare phones as vocal noise
    #        if out_phn in ['kw', 'v', 'Fy']:
    #            out_phn = 'VN'
    #        # rewriting FV and VN (fricative voicing and vocal noise) as
    #        # SPN (spoken noise)
    #        if out_phn in ['FV', 'VN']:
    #            out_phn = 'SPN'
    #        # rewriting ? as NSN (generic noise)
    #        if out_phn == '?':
    #            out_phn = 'NSN'
    #        # 2 - breaking clusters
    #        seg_1 = {
    #            'ky': 'k',
    #            'ty': 't',
    #            'ry': 'r',
    #            'cy': 't',
    #            'cj': 't',
    #            'c': 't',
    #            'py': 'p',
    #            'ny': 'n',
    #            'by': 'b',
    #            'my': 'm',
    #            'hy': 'h',
    #            'gy': 'g',
    #            'dy': 'd'
    #        }
    #        seg_2 = {
    #            'ky': 'y',
    #            'ty': 'y',
    #            'ry': 'y',
    #            'cy': 'sy',
    #            'cj': 'sj',
    #            'c': 's',
    #            'py': 'y',
    #            'ny': 'y',
    #            'by': 'y',
    #            'my': 'y',
    #            'hy': 'y',
    #            'gy': 'y',
    #            'dy': 'y'
    #        }
    #        if out_phn in seg_1:
    #            out_phns = [seg_1[out_phn], seg_2[out_phn]]
    #        else:
    #            out_phns = [out_phn]
    #            # 3 - group allophonic variants according to phonetics
    #        mapping = {
    #            'zj': 'zy',
    #            'cj': 'cy',
    #            'sj': 'sy',
    #            'nj': 'n',
    #            'kj': 'k',
    #            'hj': 'h',
    #            'gj': 'g'
    #        }
    #    
    #        out_phns = [mapping[phn] if phn in mapping else phn for phn in out_phns]
    #        if out_phns=="h:":
    #           print phn
    #        phonemes_1 = phonemes_1 + out_phns

    #        # 4 - Q before obstruent as geminate (long obstruent)
    #        if len(phonemes_1) <= 1:
    #            phonemes_2 = phonemes_1
    #        else:
    #            phonemes_2 = []
    #            previous = phonemes_1[0]

    #            for phoneme in phonemes_1[1:]:
    #                out_phn = phoneme
    #                if previous == 'Q':
    #           #print phoneme,' in ',phonemes_1
    #                    assert out_phn != 'Q', "Two successive 'Q' in phoneme sequence"
    #                    if out_phn in obstruents:
    #                        if out_phn=='z' or out_phn=='h':
    #                            print out_phn,"is about to receive :", phonemes
    #                        previous = out_phn + ':'
    #                    else:
    #                        # Q considered a glottal stop in other contexts
    #                        phonemes_2.append('Q')
    #                        previous = out_phn
    #                else:
    #                    phonemes_2.append(previous)
    #                    previous = out_phn
    #            phonemes_2.append(previous)  # don't forget last item

    #        # 5 - H after vowel as long vowel
    #        if len(phonemes_2) <= 1:
    #            # if 'H' in phonemes_2:
    #            #     self.log.debug("Isolated H: " + str(phonemes) + str(phonemes_1))
    #            phonemes_3 = phonemes_2
    #        else:
    #            phonemes_3 = []
    #            previous = phonemes_2[0]
    #            assert not(previous == 'H'), "Word starts with H"
    #            for phoneme in phonemes_2[1:]:
    #                out_phn = phoneme
    #                if out_phn == 'H':
    #                    assert previous != 'H', "Two successive 'H' in phoneme sequence"
    #                    if previous in vowels:
    #                        phonemes_3.append(previous + ':')
    #                    else:
    #                        assert previous == 'N', "H found after neither N nor vowel"
    #                        phonemes_3.append(previous)  # drop H after N
    #                    previous = 'H'
    #                else:
    #                    if previous != 'H':
    #                        phonemes_3.append(previous)
    #                    previous = out_phn
    #            if previous != 'H':
    #                phonemes_3.append(previous)  # don't forget last item
    #    for phh in phonemes_3:
    #        if phh=='z:' or phh=="h:":
    #            print phonemes_3
    #    return phonemes_3
