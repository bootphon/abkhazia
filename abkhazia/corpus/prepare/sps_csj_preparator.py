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

"""
Data preparation for Simulated Public Speaking ('S' files)
from the CSJ corpus.
Both core and non-core files are processed.
"""


import os
import sys
from collections import namedtuple
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


Utt = namedtuple('Utt', 'words start end channel')


class SPSCSJPreparator(AbstractPreparator):
    """convert the CSJ corpus to the abkhazia format"""
    name = 'sps_csj'
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

    # segment inventory based on
    # https://docs.google.com/spreadsheets/d/1a4ZWvuKfe2wMd_sVOid3KLY7PqKQkPe1uYNa_7zC5Gw/edit?pli=1#gid=0
    # with C+glide considered as two separate phonemes
    
    vowels = {
        'a': u'ä',
        'e': u'e',
        'i': u'i',
        'o': u'o',
        'u': u'ɯ',
        'a+H': u'ä:',
        'e+H': u'e:',
        'i+H': u'i:',
        'o+H': u'o:',
        'u+H': u'ɯ:'
    }

    consonants = {
        'w': u'w',
        'y': u'j',
        'm': u'm',
        'n': u'n',
        'N': u'ɴ',
        'd': u'd',
        #'Q+d': u'd:',
        't': u't',
        'Q+t': u't:',
        'c': u't͡s',
        'Q+c': u't͡s:',
        'c+y': u't͡ɕ',
        'Q+c+y': u't͡ɕ:',
        's': u's',
        'Q+s': u's:',
        's+y': u'ɕ',
        'Q+s+y': u'ɕ:',
        'z': u'z',  # fricative or affricate
        #'Q+z': u'z:',  # fricative or affricate
        'z+y': u'ʑ',  # fricative or affricate 
        #'Q+z+y': u'ʑ:',  # fricative or affricate
        'F': u'ɸ',
        #'Q+F': u'ɸ:',
        'h': u'h',
        #'Q+h': u'h:',
        'g': u'g',
        #'Q+g': u'g:',
        'k': u'k',
        'Q+k': u'k:',
        'p': u'p',
        'Q+p': u'p:',
        'r': u'r',
        'b': u'b'
        #'Q+b': u'b:'
    }

    """
    Frequencies of the various phones in the corpus
    produced by this recipe, before dropping infrequent
    phones:

        [('a', 1244643),
         ('o', 930707),
         ('i', 809173),
         ('e', 624466),
         ('k', 535058),
         ('n', 518087),
         ('u', 499639),
         ('t', 445306),
         ('m', 337715),
         ('r', 326103),
         ('s', 297367),
         ('d', 285754),
         ('N', 276768),
         ('o+H', 189680),
         ('s+y', 186292),
         ('y', 164743),
         ('g', 162616),
         ('Q+t', 108847),
         ('w', 108092),
         ('h', 92601),
         ('u+H', 82833),
         ('e+H', 81238),
         ('z+y', 76611),
         ('b', 72008),
         ('c+y', 60997),
         ('c', 54208),
         ('z', 36106),
         ('a+H', 31660),
         ('i+H', 23952),
         ('F', 20939),
         ('Q+k', 18819),
         ('p', 13239),
         ('Q+p', 10359),
         ('Q+s+y', 4791),
         ('Q+s', 4062),
         ('Q+c+y', 2851),
         ('Q+c', 1155),
         ('Q+d', 276),
         ('Q+g', 125),
         ('Q+F', 116),
         ('Q+h', 84),
         ('Q+z+y', 56),
         ('Q+z', 24),
         ('Q+b', 16)]

    To be able to train reliable phone models, we decided to
    drop from the corpus all utterances involving phones with
    less than 1000 occurrences (see 'remove_infrequent_phones' in
    __init__).
    In terms of frequency of occurrence,
    the most frequent of these phones has frequency 0.0000316
    (around 3 occurrences per 100 000 phones).

    The removed phones are: Q+b, Q+g, Q+d, Q+F, Q+h, Q+z, Q+z+y
    """

    # phones are vowels and consonents
    phones = utils.merge_dicts(vowels, consonants)

    silences = []

    variants = []


    def __init__(self, input_dir,  log=utils.logger.null_logger(),
                 copy_wavs=False):
        super(SPSCSJPreparator, self).__init__(input_dir, log)
        self.copy_wavs = copy_wavs
        # select laymen talks only
        xml_dir = os.path.join(self.input_dir, 'XML')
        self.data_files = os.listdir(xml_dir)
        self.data_files = [f.replace('.xml', '') for f in self.data_files]
        self.data_files = [f for f in self.data_files if f[0] == 'S']
        # gather label data TODO parallelize
        self.log.info('parsing {} xml files'.format(len(self.data_files)))
        self.all_utts = {}
        self.lexicon = {}
        N_parsed = 0
        N = 0
        for data in progressbar.ProgressBar()(self.data_files):
            print("xml : {}".format(data))
            utts, nb_parsed_utt, nb_utts = self.parse_xml(
                os.path.join(xml_dir,data + '.xml'))
            N_parsed = N_parsed + nb_parsed_utt
            N = N + nb_utts
            # we do not use directly the bootphon Japanese phoneset,
            # in particular we remove the + for the following phones:
            # k+y g+y n+y h+y b+y p+y m+y r+y t+y d+y
            # (i.e we consider the glide y as a separate phoneme)
            utts = break_glides_clusters(utts)
            # removing very infrequent phones 
            utts, nb_removed = remove_infrequent_phones(utts)
            self.log.info('Removed {} utts with infrequent phones'.format(nb_removed))
            N_parsed = N_parsed - nb_removed
            utts, utt_lexicon = self.lexicalize(utts)
            for utt_id in utts:
                assert not(utt_id in self.all_utts), utt_id
                self.all_utts[utt_id] = utts[utt_id]
            for word in utt_lexicon:
                if word not in self.lexicon:
                    self.lexicon[word] = utt_lexicon[word]
        proportion = 100.*N_parsed/float(N)
        self.log.info('{:.2f}% of {} utts successfully parsed'.format(proportion, N))
        print('{:.2f}% of {} utts successfully parsed'.format(proportion, N))


    def parse_xml(self, xml_file):
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
        
        # Utterance level
        nb_utts = 0;
        nb_parsed_utts = 0;
        utts = {}
        for ipu in talk.iter("IPU"):
            nb_utts = nb_utts + 1
            utt_id = spk_id + u"_" + talk_id + u"_" + ipu.attrib["IPUID"]
            channel = None
            utt_start = float(ipu.attrib["IPUStartTime"])
            utt_stop = float(ipu.attrib["IPUEndTime"])
            ipu_id = ipu.attrib["IPUID"]
            words, parse_successful = self.parse_ipu(ipu, ipu_id)
            if parse_successful:
                utts[utt_id] = Utt(words, utt_start, utt_stop, channel)
                nb_parsed_utts = nb_parsed_utts + 1
        #proportion = 100.*nb_parsed_utts/float(nb_utts)
        #print('{:.2f} percent of {} utts successfully parsed'.format(proportion,
        #                                                            nb_utts))
        return utts, nb_parsed_utts, nb_utts


    def parse_ipu(self, ipu, ipu_id):
        # Word level - Long Words Units (LUW) are taken as 'words'
        words = []
        parse_successful = True
        ipu_kanas = []
        for luw in ipu.iter("LUW"):
            # we drop any ipu where some noise occurs
            noise_in_luw = False
            for noise in luw.iter("Noise"):
                noise_in_luw = True
            if noise_in_luw:
                #print("Noise")
                ipu_kanas = None
                parse_successful = False
                break
            luw_kanas = u""
            for suw in luw.iter("SUW"):
                kanas = suw.attrib["PhoneticTranscription"]
                kanas.encode('utf8')
                luw_kanas = luw_kanas + kanas
            ipu_kanas.append(luw_kanas)
        if parse_successful:
            #print(ipu_kanas)
            ipu_kanas = u"#WB#".join(ipu_kanas)  # word boundary tag
            # appropriately deal with potential CSJ tags
            ipu_kanas = untagCSJphoneticTranscript(ipu_kanas)
            if ipu_kanas is None:
                parse_successful = False
        if parse_successful:
            # parse into phones
            words = kana2phones(ipu_kanas)
            # words.append(Word(phonemes, None, None))
            if words is None:
                parse_successful = False
            elif not(all([len(w) for w in words])):
                #print("Empty LUW in IPU {}".format(ipu_id))
                parse_successful = False 
        if not(parse_successful):
            #print("Ignoring IPU {}".format(ipu_id))
            pass
        else:
            #print(words)
            pass
        return words, parse_successful


    def lexicalize(self, utts):
        lexicon = {}
        new_utts = {}
        for utt_id in utts:
            utt = utts[utt_id]
            start = utt.start
            stop = utt.end
            words = []
            for phones in utt.words:
                assert len(phones) > 0
                assert phones != ['H']                
                word = u"-".join(phones)
                if word not in lexicon:
                    lexicon[word] = phones
                words.append(word)
                new_utts[utt_id] = {'words': words, 'start': start, 'end': stop}
        return new_utts, lexicon


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



#########################################################
############### Dealing with CSJ tags ###################
#########################################################

def untagCSJphoneticTranscript(kanas):
    """
    Deal with possible phoneticTranscription tier CSJ tags. In particular,
    returns None to indicate that the ipu should be ignored (currently this
    is when a segment contains non-phonological noise or silence or if
    there is doubt regarding transcription
    Kanas for a whole IPU are passed as argument to be able to check
    consistency of tags whose range spans several SUW or LUW
    """
    # Tags leading to drop the whole IPU
    # We do not need to care
    # about tag scope for those tags.
    tags = [u"(L", u"(笑", u"(泣", u"(咳", u"<笑>", u"<咳>", u"<息>",
            u"<P",
            u"(?", u"(O", u"(R", u"<VN>", u"<FV>"] 
    for tag in tags:
        if tag in kanas:
            #print(tag)
            kanas=None
            break
    if not kanas is None:
        # Other tags
        # simple replace patterns
        kanas = kanas.replace(u"<H>", u"")
        kanas = kanas.replace(u"<Q>", u"")
        # dealing with tags whose scope is delimited by parentheses
        # this is not the most efficient way, but it's simple to write
        changed = True
        while changed:
            changed = False
            tokens = parse_toplevel_tags(kanas)
            if tokens is None:
                kanas = None
                break
            kanas = []
            for token in tokens:
                token_kanas, changed = process_toplevel_tag(token, changed)
                if token_kanas is None:
                    kanas = None
                    break
                kanas.append(token_kanas)
            kanas = u"".join(kanas)
        return kanas


def parse_toplevel_tags(kanas):
    # xxx(tag xxx)(tag xxx; xxx)xxx(tag xxx) -> [xxx, (tag xxx),
    #                                           (tag xxx; xxx),
    #                                           xxx, (tag xxx)]
    # based on counting parentheses
    tokens = []
    open_par = 0
    last_i = -1  # index of last character of previous token
    for i, k in enumerate(kanas):
        if k==u"(":
            if i>0 and open_par == 0 and i > last_i+1:
                tokens.append(kanas[last_i+1:i])
                last_i = i-1
            open_par = open_par+1
        elif k==u")":
            open_par = open_par-1
            if open_par == 0:
                tokens.append(kanas[last_i+1:i+1])
                last_i = i
            elif open_par < 0:
                #print("Parenthesis issue: {}".format(kanas))
                tokens = None
                break
    if not(open_par == 0):
        #print("Parenthesis issue: {}".format(kanas))
        tokens = None
    # last possible token
    if not(tokens is None) and last_i < len(kanas)-1:
        tokens.append(kanas[last_i+1:])
    return tokens

    
def process_toplevel_tag(kanas, changed):
    # range tags without semicolon
    tags = [u"F", u"D", u"D2", u"M"]
    tag = startswithtag(kanas, tags)
    if not(tag is None):         
        kanas = kanas[len(tag)+2:-1]
        changed = True
    # range tags with semicolon
    kanas, changed = leftofsemicolon(kanas, [u"W", u"B"], changed)
    return kanas, changed


def startswithtag(kanas, tags):
    start_tag = None
    for tag in tags:
        if kanas[:len(tag)+2] == u"(" + tag + u" ":
            start_tag = tag
            break
    return start_tag


def leftofsemicolon(kanas, tags, changed):
    # (tag x1;x2) -> x1
    tag = startswithtag(kanas, tags)
    if not(tag is None):
        if kanas[-1] != u")":
            #print("Parenthesis issue: {}".format(kanas))
            pass
        open_par = 0
        semicolon_ind = None
        for i, k in enumerate(kanas):
            if k==u"(":
                open_par = open_par+1
            elif k==u")":
                open_par = open_par-1
            elif k==u";" and open_par==1:
                if not(semicolon_ind is None):
                    pass
                    #print(u"Several semi-colons: {}".format(kanas))
                semicolon_ind = i
        if not(open_par == 0):
            pass
            #print("Parenthesis issue: {}".format(kanas))
        elif semicolon_ind is None:
            pass
            #print(u"No semi-colons: {}".format(kanas))
        else:
            kanas = kanas[len(tag)+2:semicolon_ind]
            changed = True
    return kanas, changed    


#########################################################
############### Dealing with CSJ kanas ##################
#########################################################

def kana2phones(kanas):
    """
    Convert CSJ kanas into phonemes following the
    phonemic foldings described in:
      https://docs.google.com/spreadsheets/d/1a4ZWvuKfe2wMd_sVOid3KLY7PqKQkPe1uYNa_7zC5Gw/edit?pli=1#gid=0
    Input: 
        a unicode string of kanas from the CSJ "PhoneticTranscription"
            annotation tier containing all LUW unit for an IPU concatenated
            with u"#WB#"
    Output: None if the parsing failed or a list of lists [LUW1, LUW2, ...]
            where LUWi is the list of phonemes for the i-th LUW 
    """
    H = u"ー"

    vowel_hiragana = {u"あ" : ["a"], u"い" : ["i"], u"う" : ["u"], u"え" : ["e"], u"お" : ["o"]}
  
    small_kana = {u"ァ" : ["a"], u"ィ" : ["i"], u"ゥ" : ["u"], u"ェ" : ["e"], u"ォ" : ["o"],
                  u"ャ" : ["y a"], u"ュ" :  ["y u"], u"ョ" : ["y o"]}

    big_kana = {
        u"ア" : ["a"], 
        u"イ" : ["i"],
        u"ウ" : ["u"],
        u"エ" : ["e"],
        u"オ" : ["o"],
        u"カ" : ["k", "a"],
        u"ガ" : ["g", "a"],
        u"キ" : ["k", "i"],
        u"ギ" : ["g", "i"],
        u"ク" : ["k", "u"],
        u"グ" : ["g", "u"],
        u"ケ" : ["k", "e"],
        u"ゲ" : ["g", "e"],
        u"コ" : ["k", "o"],
        u"ゴ" : ["g", "o"],
        u"サ" : ["s", "a"],
        u"シ" : ["s+y", "i"],
        u"ス" : ["s", "u"],
        u"セ" : ["s", "e"],
        u"ソ" : ["s", "o"],
        u"ザ" : ["z", "a"],
        u"ジ" : ["z+y", "i"],
        u"ズ" : ["z", "u"],
        u"ゼ" : ["z", "e"],
        u"ゾ" : ["z", "o"],
        u"タ" : ["t", "a"],
        u"ダ" : ["d", "a"],
        u"チ" : ["c+y", "i"],
        u"ヂ" : ["z+y", "i"],
        u"ツ" : ["c", "u"],
        u"ヅ" : ["z", "u"],
        u"テ" : ["t", "e"],
        u"デ" : ["d", "e"],
        u"ト" : ["t", "o"],
        u"ド" : ["d", "o"],
        u"ナ" : ["n", "a"],
        u"ニ" : ["n", "i"],
        u"ヌ" : ["n", "u"],
        u"ネ" : ["n", "e"],
        u"ノ" : ["n", "o"],
        u"ハ" : ["h", "a"],
        u"バ" : ["b", "a"],
        u"パ" : ["p", "a"],
        u"ヒ" : ["h", "i"],
        u"ビ" : ["b", "i"],
        u"ピ" : ["p", "i"],
        u"フ" : ["F", "u"],
        u"ブ" : ["b", "u"],
        u"プ" : ["p", "u"],
        u"ヘ" : ["h", "e"],
        u"ベ" : ["b", "e"],
        u"ペ" : ["p", "e"],
        u"ホ" : ["h", "o"],
        u"ボ" : ["b", "o"],
        u"ポ" : ["p", "o"],
        u"マ" : ["m", "a"],
        u"ミ" : ["m", "i"],
        u"ム" : ["m", "u"],
        u"メ" : ["m", "e"],
        u"モ" : ["m", "o"],
        u"ヤ" : ["y", "a"],
        u"ユ" : ["y", "u"],
        u"ヨ" : ["y", "o"],
        u"ラ" : ["r", "a"],
        u"リ" : ["r", "i"],
        u"ル" : ["r", "u"],
        u"レ" : ["r", "e"],
        u"ロ" : ["r", "o"],
        u"ヮ" : ["w", "a"],
        u"ワ" : ["w", "a"],
        u"ヰ" : ["w", "i"],
        u"ヱ" : ["w", "e"],
        u"ヲ" : ["w", "o"],
        u"ン" : ["N"],
        u"ッ" : ["Q"],
        u"ー" : ["H"]
    }

    big_kana_plus_small_kana = {
        u"キャ" : ["k+y", "a"],
        u"キュ" : ["k+y",  "u"],
        u"キョ" : ["k+y", "o"],
        u"ギャ" : ["g+y", "a"],
        u"ギュ" : ["g+y", "u"],
        u"ギョ" : ["g+y", "o"],
        u"ファ" : ["F", "a"],
        u"シャ" : ["s+y", "a"],
        u"シュ" : ["s+y", "u"],
        u"ショ" : ["s+y", "o"],
        u"シェ" : ["s+y", "e"],
        u"ツェ" : ["c", "u", "e"],
        u"ジャ" : ["z+y", "a"],
        u"ジュ" : ["z+y", "u"],
        u"ジョ" : ["z+y", "o"],
        u"チャ" : ["c+y", "a"],
        u"チュ" : ["c+y", "u"],
        u"チョ" : ["c+y", "o"],
        u"ニャ" : ["n+y", "a"],
        u"ニュ" : ["n+y", "u"],
        u"ニョ" : ["n+y", "o"],
        u"ヒャ" : ["h+y", "a"],
        u"ヒュ" : ["h+y", "u"],
        u"ヒョ" : ["h+y", "o"],
        u"ヒェ" : ["h+y", "e"],
        u"ビャ" : ["b+y", "a"],
        u"ビュ" : ["b+y", "u"],
        u"ビョ" : ["b+y", "o"],
        u"ピャ" : ["p+y", "a"],
        u"ピュ" : ["p+y", "u"],
        u"ピョ" : ["p+y", "o"],
        u"ミャ" : ["m+y", "a"],
        u"ミュ" : ["m+y", "u"],
        u"ミョ" : ["m+y", "o"],
        u"リャ" : ["r+y", "a"],
        u"リュ" : ["r+y", "u"],
        u"リョ" : ["r+y", "o"],
        u"ティ" : ["t", "i"], 
        u"テュ" : ["t+y", "u"],
        u"ウォ" : ["u", "o"],
        u"ツァ" : ["c", "u", "a"],
        u"ツォ" : ["c", "u", "o"],
        u"ウィ" : ["u", "i"],
        u"チェ" : ["g+y", "e"],
        u"トゥ" : ["t", "o", "u"],
        u"ドゥ" : ["d", "o", "u"],
        u"フォ" : ["F", "u", "o"],
        u"ディ" : ["d", "e", "i"], 
        u"ジェ" : ["z+y", "e"],
        u"フェ" : ["F", "u", "e"],
        u"フィ" : ["F", "u", "i"],
        u"フュ" : ["F", "y", "u"],
        u"グヮ" : ["g", "u", "w", "a"],
        u"ウェ" : ["u", "e"],
        u"デュ" : ["d+y", "u"],
        u"スィ" : ["s", "u", "i"],
        u"ズィ" : ["z", "u", "i"],
        u"ツィ" : ["c", "u", "i"],
        u"ヴォ" : ["v", "o"],
        u"ヴァ" : ["v", "a"],
        u"イェ" : ["i", "e"],
        u"ニェ" : ["n+y", "e"]
    }

    parse_successful = True

    # First: check that input is a sequence of legal kanas 
    legal_kanas = list(vowel_hiragana.keys()) + \
                  list(small_kana.keys()) + \
                  list(big_kana.keys()) + \
                  list(big_kana_plus_small_kana.keys())
    legal_kanas = {k for s in legal_kanas for k in s}
    kanas_no_WB = kanas.replace(u"#WB#", u"")
    for kana in kanas_no_WB:
        if not(kana in legal_kanas):
            # print("Illegal kana {} in: {}".format(kana, kanas))
            parse_successful=False
            break

    # Second: parse into phones LUW by LUW
    if parse_successful:
        phonemes = []
        luws = kanas.split(u"#WB#")
        for luw in luws:
            luw_phones, parse_successful = parse_luw(luw, big_kana, small_kana,
                                                   H, big_kana_plus_small_kana,
                                                   vowel_hiragana)
            if not(parse_successful):
                break
            else:
                phonemes.append(luw_phones)

    # Third: some post-processing to get to Bootphon format for Japanese
    # phonetic transcriptions
    if parse_successful:
        phonemes, parse_successful = mergeHQluw(phonemes)  
    #previous_LUW_last_phone = None    
    old_phonemes = phonemes
    phonemes = []
    for luw_phonemes in old_phonemes:
        new_luw_phonemes = luw_phonemes
        if parse_successful:
            new_luw_phonemes, parse_successful = postprocessQ(new_luw_phonemes)
        if parse_successful:
            new_luw_phonemes, parse_successful = postprocessH(new_luw_phonemes)
        # this is different, it's more about checking that strings of sounds
        # respect a prescribed phonology (could be used for syllabification)
        #if parse_successful:
        #    new_luw_phonemes, parse_successful = postprocessN(new_luw_phonemes,
        #                                                      previous_LUW_last_phone)
        if not(parse_successful):
            break
        else:
            phonemes.append(new_luw_phonemes)
            #previous_LUW_last_phone = new_luw_phonemes[-1]
    
    # return result
    if not(parse_successful):
        phonemes = None

    return phonemes


def mergeHQluw(phonemes):
    """
    We don't want words finishing with Q or starting with H 
    because we are using a phoneset where these phones do no occur
    in isolation.
    Our solution is just to merge the two LUWs over which the geminate or
    long vowel is straddling
    """
    parse_successful = True
    new_phonemes = []
    if phonemes[0][0] == 'H':
        parse_successful = False
    if phonemes[-1][-1] == 'Q':
        parse_successful = False
    if parse_successful:
        merge_next = False
        for luw_phonemes in phonemes:
            if luw_phonemes[0] == 'H' and merge_next:
                print("QH!!")
            if luw_phonemes[0] == 'H' or merge_next:
                new_phonemes[-1] = new_phonemes[-1] + luw_phonemes
            else:
                new_phonemes.append(luw_phonemes)
            merge_next = luw_phonemes[-1] == 'Q'
    return new_phonemes, parse_successful


def parse_luw(kanas, big_kana, small_kana, H, big_kana_plus_small_kana,
              vowel_hiragana):
    phonemes = []
    parse_successful=True
    while kanas:
        if len(kanas) >= 3 and kanas[0] in big_kana and kanas[1] in small_kana and kanas[2] == H:
            # 1. big kana + small-kana + H
            phoneme_seq = big_kana_plus_small_kana[kanas[:2]]
            phoneme_seq = phoneme_seq[:-1] + [phoneme_seq[-1]+"+H"]
            phonemes = phonemes + phoneme_seq
            kanas = kanas[3:]
        elif len(kanas) >= 2 and kanas[0] in big_kana and kanas[1] in small_kana:
            # 2. big kana + small-kana
            phonemes = phonemes + big_kana_plus_small_kana[kanas[:2]]
            kanas = kanas[2:]
        elif kanas[0] in big_kana:
            # 3. big kana
            phonemes = phonemes + big_kana[kanas[0]]
            kanas = kanas[1:]
        elif len(kanas) >=2 and kanas[0] in small_kana and kanas[1] == H:
            # 4. small kana + H
            phoneme_seq = small_kana[kanas[0]]
            phoneme_seq = phoneme_seq[:-1] + [phoneme_seq[-1]+"+H"]
            phonemes = phonemes + phoneme_seq
            kanas = kanas[2:]
        elif len(kanas) >=2 and kanas[0] in vowel_hiragana and kanas[1] == H:
            # 5. vowel hiragana + H 
            phoneme_seq = vowel_hiragana[kanas[0]]
            phoneme_seq = phoneme_seq[:-1] + [phoneme_seq[-1]+"+H"]
            phonemes = phonemes + phoneme_seq
            kanas = kanas[2:]
        else:
            #print("Illegal kana pattern: {}".format(kanas[:3]))
            parse_successful=False
            break
    return phonemes, parse_successful


def postprocessQ(phonemes):
    """
    Q is attached to following non-nasal obstruents, if any,
    if none parsing fails.
    
    This is done only within LUW for now.
     
    Input and output: a list of phonemes for the LUW 
    """
    parse_successful=True
    obstruents = ["d", "d+y", "t", "t+y", "c", "c+y", "s", "s+y",
                  "z", "z+y", "F", "F+y", "h", "h+y", "g", "g+y",
                  "k", "k+y", "p", "p+y", "b", "b+y"]
    if len(phonemes) > 1:
        old_phonemes = phonemes
        phonemes = []
        previous_phone = old_phonemes[0]    
        for old_phoneme in old_phonemes[1:]:
            phoneme = old_phoneme
            if previous_phone == 'Q':
                if phoneme in obstruents:
                    previous_phone = 'Q+' + phoneme
                else:
                    #print("Illegal geminate pattern: {}".format(old_phonemes))
                    parse_successful = False
                    break
            else:
                phonemes.append(previous_phone)
                previous_phone = phoneme
        if previous_phone == 'Q':
            #print("Across LUW geminate pattern: {} ?".format(old_phonemes))
            parse_successful = False
        else:
            phonemes.append(previous_phone)  # don't forget last item
    else:
        if phonemes[0] == 'Q':
            #print("Illegal geminate pattern: {}".format(phonemes))
            parse_successful = False           
    return phonemes, parse_successful


def postprocessH(phonemes):
    # H is attached to previous vowel if any, if none, parsing fails
    parse_successful=True
    vowels = ['a', 'e', 'i', 'o', 'u']
    if len(phonemes) > 1:
        old_phonemes = phonemes
        phonemes = []
        for phoneme in old_phonemes:
            if phoneme == 'H':
                if phonemes and phonemes[-1] in vowels:
                    phonemes[-1] = phonemes[-1] + '+H'
                else:
                    #print("Illegal long vowel pattern: {}".format(phonemes))
                    parse_successful = False
                    break
            else:
                phonemes.append(phoneme)
    else:
        if phonemes[0] == 'H':
            #print("Illegal long vowel pattern: {}".format(phonemes))
            parse_successful = False
    return phonemes, parse_successful


def postprocessN(phonemes, previous_segment_last_phone=None):
    """not done anymore! this is related to phonology, not phonetic
        transcription with bootphon Japanese phoneset
    """
    # just checks that N occurrences are preceded by a vowel
    # otherwise parsing fails
    parse_successful=True
    vowels = ['a', 'e', 'i', 'o', 'u', 'a+H', 'e+H', 'i+H', 'o+H', 'u+H']
    if phonemes:
        if not(previous_segment_last_phone in vowels) and phonemes[0] == 'N':
            #print("Illegal nasal moraic pattern: {} {}".format(previous_segment_last_phone,
            #                                                   phonemes))
            parse_successful = False
    if parse_successful:
        for i in range(1, len(phonemes)):
            if phonemes[i] == 'N' and not(phonemes[i-1] in vowels):
                #print("Illegal nasal moraic pattern: {}".format(phonemes))
                parse_successful = False
                break
    return phonemes, parse_successful


#########################################################
############### Custom post-processing ##################
#########################################################


def break_cluster(phone, clusters):
    # this is completely ad hoc
    if phone in clusters:
        if 'Q' in phone:
            l = [phone[:3], phone[4]]
        else:
            l = phone.split('+')
    else:
        l = [phone]
    return l


def break_glides_clusters(utts):
    # we do not use directly the bootphon Japanese phoneset,
    # in particular we remove the + for the following phones:
    # k+y g+y n+y h+y b+y p+y m+y r+y t+y d+y
    # (i.e we consider the glide y as a separate phoneme)
    clusters = ['k+y', 'g+y', 'n+y', 'h+y', 'b+y',
                'p+y', 'm+y', 'r+y', 't+y', 'd+y',
                'Q+k+y', 'Q+g+y', 'Q+h+y', 'Q+b+y',
                'Q+p+y', 'Q+t+y', 'Q+d+y']    
    for utt_id in utts:
        utt = utts[utt_id]
        luws = utt.words
        new_luws = [[
                     e for phone in luw_phones
                            for e in break_cluster(phone, clusters)
                    ] for luw_phones in luws] 
        utts[utt_id] = Utt(new_luws, utt.start, utt.end, utt.channel)
    return utts


def remove_infrequent_phones(utts):
    # see comments below the phone inventory at the top of this file
    infrequent_phones = ['Q+d','Q+g', 'Q+F', 'Q+h', 'Q+z+y', 'Q+z', 'Q+b']
    utts2remove = []
    for utt_id in utts:
        drop_utt = False
        utt = utts[utt_id]
        luws = utt.words
        for luw_phones in luws:
            if any([phone in infrequent_phones for phone in luw_phones]):
                drop_utt= True
                break
        if drop_utt:
            utts2remove.append(utt_id)
    for utt_id in utts2remove:
        del utts[utt_id]
    return utts, len(utts2remove)
