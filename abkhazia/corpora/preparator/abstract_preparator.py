"""Provides a base class for corpora preparation in the abkhazia format"""

import codecs
import os

from abkhazia.corpora.utils import DEFAULT_OUTPUT_DIR
from abkhazia.utilities.log2file import get_log
import abkhazia.corpora.validation


class AbstractPreparator(object):
    """This class is a common wrapper to all the corpus preparators

    TODO description of attributes, explications on what is abstract
    and what is not.

    For more details on data preparation, please refer to
    https://github.com/bootphon/abkhazia/wiki/data_preparation

    """
    def __init__(self, input_dir, output_dir=None, verbose=False):
        self.verbose = verbose

        # init input directory
        if not os.path.isdir(input_dir):
            raise IOError(
                'input directory does not exist: {}'.format(input_dir))
        self.input_dir = os.path.abspath(input_dir)

        # init output directory
        if output_dir is None:
            self.output_dir = os.path.join(DEFAULT_OUTPUT_DIR, self.name)
        else:
            self.output_dir = os.path.abspath(output_dir)

        # init output subdirectories hierarchy
        self.data_dir = os.path.join(self.output_dir, 'data')
        self.wavs_dir = os.path.join(self.data_dir, 'wavs')
        if os.path.exists(self.data_dir):
            raise IOError(
                'output directory already exists: {}'.format(self.data_dir))
        os.makedirs(self.wavs_dir)

        # init output files that will be populated by prepare()
        fname = lambda name: os.path.join(self.data_dir, name)
        self.segments_file = fname('segments.txt')
        self.speaker_file = fname('utt2spk.txt')
        self.transcription_file = fname('text.txt')
        self.lexicon_file = fname('lexicon.txt')
        self.phones_file = fname('phones.txt')
        self.variants_file = fname('variants.txt')
        self.silences_file = fname('silences.txt')

        # create the log dir if not existing
        self.logs_dir = os.path.join(self.output_dir, 'logs')
        try:
            os.makedirs(self.logs_dir)
        except os.error:
            pass

        # init the log with the log2file module
        self.log = get_log(os.path.join(self.logs_dir, 'data_preparation.log'),
                           self.verbose)
        self.log.info('{} preparator created, read from {}'
                      .format(self.name, self.input_dir))

    def prepare(self):
        """Prepare the corpus from raw distribution to abkhazia format"""
        # prepare the corpus step by step
        self.link_wavs()
        self.make_segment()
        self.make_speaker()
        self.make_transcription()
        self.make_lexicon()
        self.make_phones()

    def validate(self):
        """Return True if the TODO"""
        print('validating the prepared {} corpus'.format(self.name))
        abkhazia.corpora.validation.validate(self.output_dir, self.verbose)

    def make_phones(self):
        """Create phones, silences and variants list files

        The phone inventory contains a list of each symbol used in the
        pronunciation dictionary

        TODO document silences and variants

        phones.txt: <phone-symbol> <ipa-symbol>

        """
        with codecs.open(self.phones_file, mode='w', encoding='UTF-8') as out:
            for phone in self.phones:
                out.write(u'{0} {1}\n'.format(phone, self.phones[phone]))

        if self.silences:
            with codecs.open(self.silences_file, 'w', encoding='UTF-8') as out:
                out.write(u'\n'.join(self.silences))

        if self.variants:
            with codecs.open(self.variants_file, 'w', encoding='UTF-8') as out:
                for var in self.variants:
                    out.write(u" ".join(var) + u"\n")

        print('finished creating phones.txt, silences.txt, variants.txt')


    ############################################
    #
    # The above functions are abstracts and must be implemented by
    # child classes for each supported corpus.
    #
    ############################################

    name = ''
    """The name of the corpus"""

    phones = {}
    """A dict associating each phone in corpus with it's pronunciation"""

    silences = []
    """TODO document"""

    variants = []
    """TODO document"""

    def link_wavs(self):
        """Links the corpus speech folder to the output directory

        Populate self.wavs_dir with symbolic links to the corpus
        speech files. Optionnaly rename them.

        """
        raise NotImplementedError

    def make_segment(self):
        """Create utterance file

        Populate self.segments_file with the list of all utterances
        with the name of the associated wavefiles.

        If there is more than one utterance per file, the start and
        end of the utterance in that wavefile expressed in seconds.

        segments.txt: <utterance-id> <wav-file> [<segment-begin> <segment-end>]

        """
        raise NotImplementedError

    def make_speaker(self):
        """Create speaker file

        Populate self.speaker_file with the list of all utterances
        with a unique identifier for the associated speaker.

        utt2spk.txt: <utterance-id> <speaker-id>

        """
        raise NotImplementedError

    def make_transcription(self):
        """Create transcription file

        Populate self.transcription_file with the transcription in
        word units for each utterance

        text.txt: <utterance-id> <word1> <word2> ... <wordn>

        """
        raise NotImplementedError

    def make_lexicon(self):
        """Create phonetic dictionary file

        The phonetic dictionary contains a list of words with their
        phonetic transcription

        lexicon.txt: <word> <phone_1> <phone_2> ... <phone_n>

        """
        raise NotImplementedError
