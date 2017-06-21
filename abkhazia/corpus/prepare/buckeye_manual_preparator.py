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
Data preparation for the Buckeye corpus (Bootphon revised version)
using manual transcriptions.
"""

import collections
import numpy as np
import os
import re

import abkhazia.utils as utils
from abkhazia.corpus.prepare import AbstractPreparator


class BuckeyeManualPreparator(AbstractPreparator):
    """Convert the Buckeye corpus to the abkhazia format"""

    name = 'buckeye_manual'
    url = 'http://buckeyecorpus.osu.edu'
    audio_format = 'wav'
    description = 'Buckeye Corpus of conversational speech'
    long_description = '''
    The Buckeye Corpus of conversational speech contains high-quality
    recordings from 40 speakers in Columbus OH conversing freely with
    an interviewer. The speech has been orthographically transcribed
    and phonetically labeled. The audio and text files, together with
    time-aligned phonetic labels, are stored in a format for use with
    speech analysis software (Xwaves and Wavesurfer). Software for
    searching the transcription files is currently being written. The
    corpus is FREE for noncommercial uses.

    This project is funded by the National Institute on Deafness and
    other Communication Disorders and the Office of Research at Ohio
    State University.'''

      # The inventory is chosen to match the WSJ phoneset
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
        'R': u'ɹ',
        'W': u'w',
        'Y': u'j',
        'HH': u'h'
    }
    
    """
    Phone counts in the final corpus before allophone folding:
    [('ah', 68008), ('ih', 60740), ('n', 47634), ('s', 40070), ('eh', 35068),
     ('t', 32558), ('iy', 32132), ('r', 29327), ('k', 25998), ('l', 25798),
     ('m', 25610), ('d', 22525), ('ay', 22217), ('w', 20253), ('dh', 19104),
     ('ae', 18158), ('z', 17813), ('ow', 17547), ('er', 16858), ('b', 15311),
     ('ey', 14376), ('aa', 14221), ('dx', 13574), ('y', 13562), ('p', 13342),
     ('f', 12303), ('v', 11569), ('hh', 11557), ('tq', 11278), ('uw', 10916),
     ('g', 9403), ('ng', 8556), ('nx', 8534), ('ao', 8166), ('th', 7662),
     ('en', 5945), ('uh', 5845), ('sh', 5659), ('aw', 4850), ('ch', 4544),
     ('jh', 4342), ('el', 3975), ('em', 2947), ('zh', 948), ('oy', 528),
     ('eng', 144)]
    Total: 801475
     
    After allophone folding:
    [('ah', 68008), ('n', 62113), ('ih', 60740), ('t', 52370), ('s', 40070),
     ('d', 36099), ('eh', 35068), ('iy', 32132), ('l', 29773), ('r', 29327),
     ('m', 28557), ('k', 25998), ('ay', 22217), ('w', 20253), ('dh', 19104),
     ('ae', 18158), ('z', 17813), ('ow', 17547), ('er', 16858), ('b', 15311),
     ('ey', 14376), ('aa', 14221), ('y', 13562), ('p', 13342), ('f', 12303),
     ('v', 11569), ('hh', 11557), ('uw', 10916), ('g', 9403), ('ng', 8700),
     ('ao', 8166), ('th', 7662), ('uh', 5845), ('sh', 5659), ('aw', 4850),
     ('ch', 4544), ('jh', 4342), ('zh', 948), ('oy', 528)]
    Total: 810009 (the 8534 nx are divided into n + t)

    """
    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []


    def __init__(self, input_dir, log=utils.logger.null_logger(),
                 copy_wavs=False):
        super(BuckeyeManualPreparator, self).__init__(input_dir, log=log)
        self.copy_wavs = copy_wavs
        # the input files we will parse
        phone_files = self._list_files('.phones_fold')
        word_files = [f.replace('.phones_fold', '.words_fold') for f in phone_files]
        self.segments, self.utt2spk, self.text = parse_corpus(phone_files,
                                                              word_files)

    def _list_files(self, ext, exclude=None, abspath=False, realpath=False):
        files = utils.list_files_with_extension(
            self.input_dir, ext, abspath=abspath, realpath=realpath)

        if exclude is not None:
            files = [f for f in files for e in exclude if e not in f]

        return files

    def list_audio_files(self):
        return self._list_files('.wav', abspath=True, realpath=True)

    def make_segment(self):
        return self.segments

    def make_speaker(self):
        return self.utt2spk

    def make_transcription(self):
        return self.text

    def make_lexicon(self):
        """Build the buckeye lexicon from the text.
            As for the CSJ recipe, different phonetic realizations
            of a same word (as described by the manual annotations)
            are considered as different words.
            For example: okay pronounced as "o k ay" vs "k ay".
        """
        lexicon = {}
        for utt_id in self.text:
            words = self.text[utt_id].split(" ")
            for word in words:
                if not(word in lexicon):
                    lexicon[word] = word.replace("-", " ").upper()
        return lexicon


Utt = collections.namedtuple('Utt', 'words start end')


def parse_word_line(line):
    """
    Returns the word/speech event label, the corresponding manual transcription
    and the time of the end of the word in seconds
    """
    match = re.match(
        r'\s*(.*)\s+(121|122)\s(.*);(.*); (.*); (.*)', line)
    assert match, line
    time = float(match.group(1))
    label = match.group(3)
    manual_transcription = match.group(5)
    return label, manual_transcription, time


def parse_word_file(word_file):
    words = []
    manual_transcripts = []
    end_times = []
    with open(word_file, 'r') as fh:
        lines = fh.readlines()
    for line in lines[9:]:  # skip header
        #line = line.strip()
        label, manual_transcription, time = parse_word_line(line)
        words.append(label)
        manual_transcripts.append(manual_transcription)
        end_times.append(time)
    return words, manual_transcripts, np.array(end_times)


def parse_phone_line(line):
    match = re.match(
        r'\s*(.*)\s+(121|122)\s(.*)', line)
    assert match, line
    time = float(match.group(1))
    label = match.group(3)    
    return label, time


def parse_phone_file(phone_file):
    phones = []
    end_times = []
    with open(phone_file, 'r') as fh:
        lines = fh.readlines()
    for line in lines[9:]:  # skip header
        #line = line.strip()
        phone, end_time = parse_phone_line(line)
        phones.append(phone)
        end_times.append(end_time)  
    return phones, np.array(end_times)


def get_phones(phones, phone_endtimes, from_time, to_time):
    success = True
    ind = np.where(phone_endtimes == from_time)[0]
    if ind:
        assert len(ind) == 1, from_time
        start_index = ind[0]+1
    else:
        # mismatch between word and phone level alignments
        # could check closest phone + previous phones from the word tier
        success=False
    ind = np.where(phone_endtimes == to_time)[0]
    if ind:
        assert len(ind) == 1, to_time
        end_index = ind[0]
    else:
        # mismatch between word and phone level alignments
        # could check closest phone + next phones from the word tier
        success = False
    if success:
        #print("Fragment retrieved from phone alignment")
        res = phones[start_index:end_index+1]
        if "IVER" in res:
            success = False
            res = None
        else:
            res = " ".join(res)
    else:
        #print("Mismatch between word and phone level alignments")
        res = None
    return res


def parse_utterances(words, manual_transcripts, end_times,
                     phones, phone_endtimes):
    # any word label beginning with one of the following is considered
    # as an utterance boundary label
    utterance_boundary_prefixes = ["<LAUGH", "<VOCNOISE", "<NOISE", "<IVER",
                                   "<SIL>", "<EXCLUDE", "<UNKNOWN", "{B_TRANS}",
                                   "{E_TRANS}"]
    # <VOICE=xxx>, <IVER_overlap-start>, <IVER_overlap-end>, <CONF=M>, <CONF=L>
    #{B_THIRD_SPK}, {E_THID_SPK} are not present in LSCP version of Buckeye
    
    # word label beginning with one of the following have a transcription
    # but it needs to be fetched from the phone_fold file
    speech_event_prefixes = ["<EXT", "<HES", "<CUTOFF", "<ERROR"]
    # <SYLSTRESS-word=xxxx>, <voiceless-vowel> are not present in LSCP version
    # of Buckeye
    
    utts = []
    current_utt = []
    current_utt_start = None
    previous_word_end = None
    for word_label, transcript, t in zip(words, manual_transcripts, end_times):
        if any([p in word_label for p in utterance_boundary_prefixes]):
            # utterance boundary
            if current_utt:
                utts.append(Utt(current_utt, 
                                current_utt_start,
                                previous_word_end))
            current_utt = []
            current_utt_start = t
        elif any([p in word_label for p in speech_event_prefixes]):
            # hesitation, word fragment, etc. where the manual transcription
            # is not in the word_fold file and needs to be fetched from the
            # phone_fold file
            event_phones = get_phones(phones, phone_endtimes,
                                      from_time=previous_word_end,
                                      to_time=t)
            current_utt.append(event_phones)
        else:
            if "{" in word_label or "<" in word_label:
                print("Broken word label:" + word_label)
                raise ValueError
            # normal speech; add the manual transcript to current utterance
            current_utt.append(transcript)
        previous_word_end = t
    return utts


def phone_counts(utts):
    phones = [phone
                for _, utt in utts
                    for word in utt.words if not(word is None)
                        for phone in word.split(" ")]
    c = collections.Counter(phones)
    return c


def filter_broken_utts(all_utts):
    """
    Filter out remaining utterances with non-speech content. Most of these
    are probably due to some remaining consistency issues within the corpus.
    This includes cutoffs/hesitation etc. where the alignment in the word_fold
    and phone_fold files do not exactly match, tags that are missing or
    incorrectly orthographied, within word silences and noise, words with
    missing manual transcriptions... 
    We also remove utterances containing phones that are not really used
    (less than 10 occurrences overall in the corpus)
    It's a small proportion of the total corpus, so we just ignore these utterances
    """   
    expected_phoneset = {'ch', 'uh', 'dx', 'o', 'en', 'r', 'p', 'hh', 'ao',
                         'ey', 'iy', 'ih', 'nx', 'tq', 'm', 'sh', 'l',
                         'aa', 'n', 'h', 'em', 'k', 'ihn', 't', 'th', 'el',
                         'v', 'w', 'er', 'aw', 'y', 'd', 'jh', 'zh', 'z',
                         'dh', 'uw', 'ow', 'f', 'ay','ah', 'g', 'b', 'ng',
                         'eng', 'oy', 'ae', 'eh', 's'}
     
    counts = phone_counts(all_utts)
    print(counts.most_common())
    for phone in counts:
        if counts[phone] < 10 and phone in expected_phoneset:
            print("Removing phone {} occurring {} times".format(phone,
                                                                counts[phone]))
            expected_phoneset.remove(phone)
    """
    Removes: ('h', 4), ('o', 1), ('ihn', 1)
    +
    ('', 27)('VOCNOISE_WW', 8)('SIL', 6)('SIL_WW', 6)('CUTOFF', 5)
    ('NOISE_WW', 4)('VOCNOISE', 4)('UNKNOWN', 3)('LAUGH', 3)('NOISE', 2)
    ('UNKNOWN_WW', 2)('ERROR', 1)('EXCLUDE', 1)('LENGTH_TAG', 1)
    """
    utts = []
    for record_id, utt in all_utts:
        keep_utt = True
        for word in utt.words:
            if word is None:
                keep_utt = False
            else:
                for phone in word.split(" "):
                    if not(phone in expected_phoneset):
                        keep_utt = False
                        break
        if keep_utt:
            utts.append((record_id, utt))
    proportion_kept = 100*len(utts)/float(len(all_utts))
    print("{:.2f} % of {} utterances successfully parsed".format(
          proportion_kept, len(all_utts)
         ))
    return utts


def fold_allophones(utts):
    # em->m, en->n, eng->ng, el->l, dx->d, tq->t, nx->nt
    foldings = {'em': ['m'], 
                'en': ['n'],
                'eng': ['ng'],
                'el': ['l'],
                'dx': ['d'],
                'tq': ['t'],
                'nx': ['n', 't']}
    folded_utts = []
    for record_id, utt in utts:
        folded_words = []
        for word in utt.words:
            folded_phones = [foldings[phone] if phone in foldings else [phone]
                                for phone in word.split(" ")]
            folded_phones = [phone for phone_list in folded_phones
                                       for phone in phone_list]
            folded_words.append(" ".join(folded_phones))
        folded_utts.append((record_id, Utt(folded_words, utt.start, utt.end)))
    return folded_utts


def parse_corpus(phone_files, word_files):
    all_utts = []
    for phone_file, word_file in zip(phone_files, word_files):
        # log.info('loading %s', os.path.basename(word_file))
        # /path/to/.../s2202b.txt -> s2202b -> s22
        record_id = os.path.splitext(os.path.basename(word_file))[0]
        speaker_id = record_id[:3]
        phones, phone_endtimes = parse_phone_file(phone_file)
        words, manual_transcription, word_endtimes = parse_word_file(word_file)
        utts = parse_utterances(words, manual_transcription, word_endtimes,
                                phones, phone_endtimes)        
        all_utts = all_utts + [(record_id, utt) for utt in utts]
    # remove broken utts
    utts = filter_broken_utts(all_utts)
    # fold allophonic variants
    utts = fold_allophones(utts)
    print(phone_counts(utts).most_common())
    # format output
    segments = {}
    utt2spk = {}
    text = {}
    previous_record_id = None
    ident = 0
    for record_id, utt in utts:
        speaker_id = record_id[:3]
        if previous_record_id != record_id:
            ident=0
        ident = ident+1
        previous_record_id = record_id
        utt_id = record_id + "_" + str(ident)
        assert not(utt_id in text)
        text[utt_id] = " ".join([word.replace(" ", "-") for word in utt.words])
        segments[utt_id] = (record_id + '.wav', utt.start, utt.end)
        utt2spk[utt_id] = speaker_id  
    return segments, utt2spk, text
