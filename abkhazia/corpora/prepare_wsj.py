#!/usr/bin/env python
# coding: utf-8

"""Data preparation for the Wall Street Journal corpus"""

import codecs
import os
import re

from abkhazia.corpora.utils import AbstractPreparator
from abkhazia.corpora.utils import list_directory
from abkhazia.corpora.utils import sph2wav
from abkhazia.corpora.utils import default_argument_parser


def rewrite_wsj_word(w):
    """Return empty string to indicate that the word should be ignored"""
    assert not w == '', 'Empty word'

    # Upcase everything to match the CMU dictionary
    w = w.upper()

    # Remove backslashes as we don't need the quoting
    w = w.replace('\\', '')

    # Normalization for Nov'93 test transcripts
    w = w.replace('%PERCENT', 'PERCENT').replace('.POINT', 'POINT')

    # the <> means verbal deletion of a word, we just remove brackets
    if w[0] == '<' and w[-1] == '>':
        w = w[1:-1]

    # '~' used to indicate truncation of an utterance. Not a word.
    if w == '~':
        return ''

    # '.' used to indicate a pause, not included in the transcript for
    # now. (could use a special SIL word in the dictionary for this)
    if w == '.':
        return ''

    # E.g. [<door_slam], this means a door slammed in the preceding
    # word. we remove it from the transcript and keep the preceding
    # word. (could replace the preceding word by <NOISE>)
    if w[:1] == '[<' and w[-1] == ']':
        return ''

    # E.g. [door_slam>], this means a door slammed in the next word.
    # we remove it from the transcript and keep the next word.  (could
    # replace the next word by <NOISE>)
    if w[0] == '[' and w[-2:] == '>]':
        return ''

    # E.g. [phone_ring/], which indicates the start of this
    # phenomenon.  we remove it from the transcript and keep the part
    # where the phone rings.  (could replace the whole part where the
    # phone rings by <NOISE>)
    if w[0] == '[' and w[-2:] == '/]':
        return ''

    # E.g. [/phone_ring], which indicates the end of this phenomenon.
    # we remove it from the transcript and keep the part where the
    # phone rings.  (could replace the whole part where the phone
    # rings by <NOISE>)
    if w[:1] == '[/' and w[-1] == ']':
        return ''

    # Other noise indications, e.g. [loud_breath].  We replace them by
    # the generic <NOISE> marker
    if w[0] == '[' and w[-1] == ']':
        return '<noise>'

    # This is a common issue; the CMU dictionary has it as -DASH.
    if w == '--DASH':
        return '-DASH'

    # if we reached this point without returning, return w as is
    return w


class WallStreetJournalPreparator(AbstractPreparator):
    """Convert the WSJ corpus to the abkhazia format"""
    def __init__(self, input_dir, cmu_dict,
                 output_dir=None, verbose=False, overwrite=False):
        # call the AbstractPreparator __init__
        super(WallStreetJournalPreparator, self).__init__(
            input_dir, output_dir, verbose, overwrite)

        # init path to CMU dictionary
        if not os.path.isfile(cmu_dict):
            raise IOError(
                'CMU dictionary does not exist: {}'
                .format(cmu_dict))
        self.cmu_dict = cmu_dict

        # Listing files for the relevant part using the following 2
        # criterions:
        # - files are nested within self.dir_pattern
        # - the 4th letter in the file name is self.file_pattern

        # For WSJ_journalist_read, select the file pattern: 'si_tr_j'
        # si = Speaker-Independent vs sd = Speaker-Dependent tr =
        # Training data j = Journalist read c = common read speech as
        # opposed to Spontaneous, Adaptation read
        dir_filter = lambda d: d in self.dir_pattern
        filter_dot = lambda f: f[3] == self.file_pattern and f[-4:] == '.dot'
        filter_wv1 = lambda f: f[3] == self.file_pattern and f[-4:] == '.wv1'

        self.input_recordings = self.list_files(dir_filter, filter_wv1)
        self.input_transcriptions = self.list_files(dir_filter, filter_dot)
        self.bad_utts = self.find_corrupted_utts(self.input_transcriptions)

    dir_pattern = None

    file_pattern = None

    name = 'WSJ'

    # IPA transcription of the CMU phones
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
        'HH': u'h'
    }

    silences = [u"NSN"]  # SPN and SIL will be added automatically

    variants = []  # could use lexical stress variants...

    # TODO review and simplify this function, only one os.walk
    def list_files(self, dir_filter, file_filter):
        """Return a list of abspaths to relevant WSJ files"""
        matched = []
        for dirs_path, dirs, _ in os.walk(self.input_dir):
            for d in dirs:
                if dir_filter(d):
                    for d_path, _, files in os.walk(os.path.join(dirs_path, d)):
                        matched += [os.path.join(d_path, f) for f in files if file_filter(f)]
        return matched


    def find_corrupted_utts(self, dot_files):
        """Return the list of bad recordings found in utterances files

        The tag '[bad_recording]' in a transcript file indicates there
        is a problem with the associated recording (if it even exists)
        so exclude it

        """
        bad_utts = []
        for f in dot_files:
            for line in codecs.open(f, mode='r', encoding='UTF-8').readlines():
                if '[bad_recording]' in line:
                    utt_id = re.match(r'(.*) \((.*)\)', line).group(2)
                    bad_utts.append(utt_id)
        # TODO log the results if any
        return bad_utts

    def link_wavs(self):
        # convert the list of input audio files to wav
        for sph in self.input_recordings:
            utt_id = os.path.basename(sph).replace('.wv1', '')
            if utt_id not in self.bad_utts:  # exclude some utterances
                wav = os.path.join(self.wavs_dir, utt_id + '.wav')
                sph2wav(sph, wav)
        self.log.debug('converted all files to wav')


    def make_segment(self):
        with codecs.open(self.segments_file, 'w', encoding='UTF-8') as out:
            for wav in list_directory(self.wavs_dir):
                utt_id = os.path.basename(wav).replace('.wav', '')
                out.write(u"{0} {1}\n".format(utt_id, wav))
        self.log.debug('finished creating segments file')


    def make_speaker(self):
        with codecs.open(self.speaker_file, 'w', encoding='UTF-8') as out:
            for wav in list_directory(self.wavs_dir):
                utt_id = os.path.basename(wav).replace('.wav', '')
                # speaker_id are the first 3 characters of the filename
                out.write(u"{0} {1}\n".format(utt_id, utt_id[:3]))
        self.log.debug('finished creating utt2spk file')


    def make_transcription(self):
        # concatenate all the transcription files
        transcription = []
        for trs in self.input_transcriptions:
            transcription += codecs.open(trs, 'r', encoding='UTF-8').readlines()

        # parse each line and write it to output file in abkhazia format
        with codecs.open(self.transcription_file, 'w', encoding='UTF-8') as out:
            for line in transcription:
                # parse utt_id and text
                matches = re.match(r'(.*) \((.*)\)', line.strip())
                text = matches.group(1)
                utt_id = matches.group(2)

                # skip bad utterances
                if utt_id not in self.bad_utts:
                    # TODO is it still required ?
                    # # correct some defect in original corpus (ad hoc)
                    # if utt_id == '400c0i2j':
                    #     text = text.replace('  ', ' ')

                    # re-format text and remove empty words
                    words = [rewrite_wsj_word(w) for w in text.split(' ')]
                    text = ' '.join([w for w in words if w != ''])

                    # output to file
                    out.write(u"{0} {1}\n".format(utt_id, text))

        self.log.debug('finished creating text file')


    def make_lexicon(self):
        open_utf8 = lambda f, m: codecs.open(f, mode=m, encoding='UTF-8')

        with open_utf8(self.lexicon_file, 'w') as out:
            for line in open_utf8(self.cmu_dict, 'r').readlines():
                # remove newline and trailing spaces
                line = line.strip()

                # skip comments
                if not (len(line) >= 3 and line[:3] == u';;;'):
                    # parse line
                    word, phones = line.split(u'  ')

                    # skip alternative pronunciations, the first one
                    # (with no parenthesized number at the end) is
                    # supposed to be the most common and is retained
                    if not re.match(ur'(.*)\([0-9]+\)$', word):
                        # ignore stress variants of phones
                        phones = re.sub(u'[0-9]+', u'', phones)
                        # write to output file
                        out.write(u"{0} {1}\n".format(word, phones))

            # add special word: <noise> NSN. special word <unk> SPN
            # will be added automatically during corpus validation but
            # it would make sense if to add it here if we used it for
            # some particular kind of noise, but this is not the case
            # at present
            out.write(u"<noise> NSN\n")
        self.log.debug('finished creating lexicon file')


# TODO check if that's correct (in particular no sd_tr_s or l in WSJ1
# and no si_tr_l in WSJ0 ??)

class JournalistReadPreparator(WallStreetJournalPreparator):
    # For WSJ_journalist_read, select the file pattern: 'si_tr_j'
    # si = Speaker-Independent vs sd = Speaker-Dependent tr =
    # Training data j = Journalist read c = common read speech as
    # opposed to Spontaneous, Adaptation read
    name = WallStreetJournalPreparator.name + '_journalist_read'
    dir_pattern = ['si_tr_j']
    file_pattern = 'c'

class JournalistSpontaneousPreparator(WallStreetJournalPreparator):
    #For WSJ_journalist_spontaneous, we selected the following
    #types of files: 'si_tr_j' si = Speaker-Independent tr =
    #Training data jd = Spontaneous Journalist Dictation s =
    #Spontaneous no/unspecified verbal punctuation as opposed to
    #Common read speech, Adaptation read
    name = WallStreetJournalPreparator.name + '_journalist_spontaneous'
    dir_pattern = ['si_tr_jd']
    file_pattern = 's'

class MainReadPreparator(WallStreetJournalPreparator):
    #For WSJ_main_read, we selected the following types of files:
    #'si_tr_s', 'si_tr_l', 'sd_tr_s', 'sd_tr_l' si =
    #Speaker-Independent vs sd = Speaker-Dependent tr = Training
    #data s = standard subjects need to read approximately 260
    #sentences vs l: long sample - these subjects have more
    #sentences: 1800 c = common read speech as opposed to
    #Spontaneous, Adaptation read
    name = WallStreetJournalPreparator.name + '_main_read'
    dir_pattern = ['si_tr_s', 'si_tr_l', 'sd_tr_s', 'sd_tr_l']
    file_pattern = 'c'


# To deal with specific WSJ command line arguments, we can't use the
# default corpora.utils.main function
def main():
    """The command line entry for WSJ corpus preparation"""
    try:
        # mapping of the three WSJ variations
        preparators = {
            'journalist_read': JournalistReadPreparator,
            'journalist_spontaneous': JournalistSpontaneousPreparator,
            'main_read': MainReadPreparator
        }

        # add WSJ specific arguments to the parser
        parser = default_argument_parser(
            WallStreetJournalPreparator.name, __doc__)

        parser.add_argument('-t', '--type', choices=preparators.keys(),
                            help='the subpart of WSJ to prepare')

        parser.add_argument('cmu_dict', help='the CMU dictionary '
                            'file to use for lexicon generation')

        # parse command line arguments
        args = parser.parse_args()

        # prepare the corpus
        corpus_prep = preparators[args.type](
            args.input_dir, args.cmu_dict,
            args.output_dir, args.verbose, args.overwrite)

        corpus_prep.prepare()

        if not args.no_validation:
            corpus_prep.validate()

    except Exception as err:
        print('fatal error: {}'.format(err))

if __name__ == '__main__':
    main()
