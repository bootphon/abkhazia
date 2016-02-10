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

"""Provides a base class for corpus preparation in the abkhazia format"""

import os
from pkg_resources import Requirement, resource_filename

from abkhazia.utils import get_log, open_utf8
from abkhazia.corpora.utils import validation, DEFAULT_OUTPUT_DIR


class AbstractPreparator(object):
    """This class is a common wrapper to all the corpus preparators

    The AbstractPreparator class provides the basic functionalities
    all preparators rely on for the conversion of a specific corpus to
    the abkhazia format. It also proposes a set of abstract methods
    (ie an interface) that each specialized prepartor must
    implement. Those methods correspond to the corpus preparation
    successive steps.

    This class is not to be used directly and must be inherited by
    specialized preparators.

    For more details on data preparation and the abkhazia format,
    please refer to
    https://github.com/bootphon/abkhazia/wiki/data_preparation

    Parameters
    ----------

    The following parameters are specified when initializing a new
    preparator.

    'input_dir' : The input directory containing the raw distribution
        of the corpus to prepare. This directory must exists on the
        filesystem.

    'output_dir' : The output directory where to write the prepared
        version of the corpus. If not specified, a default directory
        is guessed based on the corpus name.

    'verbose' : This argument serves as initialization of the log2file
        module. See there for more documentation.

    Methods
    -------

    From a user perspective, the most important methods offered by the
    abstract preparator are prepare() and validate().

    prepare(): convert the original data in 'input_dir' to a corpus in
        the abkhazia format, store the data in 'output_dir'

    validate(): after preparation, checks the created corpus is
        compatible with abkhazia

    """
    def __init__(self, input_dir, output_dir=None, verbose=False):
        self.verbose = verbose

        # init input directory
        if not os.path.isdir(input_dir):
            raise IOError(
                'input directory does not exist:\n{}'.format(input_dir))
        self.input_dir = os.path.abspath(input_dir)

        # init output directory
        if output_dir is None:
            self.output_dir = os.path.join(DEFAULT_OUTPUT_DIR, self.name)
        else:
            self.output_dir = os.path.abspath(output_dir)

        # create the log directory if not existing
        self.logs_dir = os.path.join(self.output_dir, 'logs')
        if not os.path.isdir(self.logs_dir):
            os.makedirs(self.logs_dir)

        # init the log with the log2file module
        self.log = get_log(os.path.join(self.logs_dir, 'data_preparation.log'),
                           self.verbose)

        # create empty hierarchy output_dir/data/wavs
        self.data_dir = os.path.join(self.output_dir, 'data')
        self.wavs_dir = os.path.join(self.data_dir, 'wavs')
        if (not os.path.isdir(self.wavs_dir) and
            not os.path.islink(self.wavs_dir)):
            os.makedirs(self.wavs_dir)

        # init output files that will be populated by prepare()
        fname = lambda name: os.path.join(self.data_dir, name + '.txt')
        self.segments_file = fname('segments')
        self.speaker_file = fname('utt2spk')
        self.transcription_file = fname('text')
        self.lexicon_file = fname('lexicon')
        self.phones_file = fname('phones')
        self.variants_file = fname('variants')
        self.silences_file = fname('silences')

        self.log.info('creating {} preparator'.format(self.name))


    def prepare(self):
        """Prepare the corpus from raw distribution to abkhazia format

        This method must not be overloaded in child classes as it
        ensure consistency with the abkhazia format.

        """
        self.log.info('writing to {}'.format(self.data_dir))

        # the successive preparation steps associated with the target
        # they will populate
        steps = [
            (self.make_wavs, self.wavs_dir),
            (self.make_segment, self.segments_file),
            (self.make_speaker, self.speaker_file),
            (self.make_transcription, self.transcription_file),
            (self.make_lexicon, self.lexicon_file),
            (self.make_phones, self.phones_file)
        ]

        # run each step one after another
        for step, target in steps:
            self.log.info('preparing {}'.format(os.path.basename(target)))
            step()

    def validate(self):
        """Check that the prepared data conforms to the abkhazia format

        This method must not be overloaded in child classes as it
        ensure consistency with the abkhazia format.

        """
        self.log.info('validating the prepared {} corpus'.format(self.name))
        validation.validate(self.output_dir, self.verbose)

    def make_phones(self):
        """Create phones, silences and variants list files

        The phone inventory contains the list of each symbol used in
        the pronunciation dictionary, mapped to their IPA symbol.

        The silences inventory contains the list of each symbol used
        to represent a silence.

        The variants inventory contains the list of tonal variants
        associated with the phones. For most corpora, there is no
        variants and this list is kept empty.

        phones.txt: <phone-symbol> <ipa-symbol>

        silences.txt: <silence-symbol>

        variants.txt: <phone_variant_1 phone_variant_2 ... phone_variant_n>


        """
        with open_utf8(self.phones_file, 'w') as out:
            for phone in self.phones:
                out.write(u'{0} {1}\n'.format(phone, self.phones[phone]))
        self.log.debug('writed {}'.format(self.phones_file))

        if self.silences is not []:
            with open_utf8(self.silences_file, 'w') as out:
                for sil in self.silences:
                    out.write(sil + u"\n")
            self.log.debug('writed {}'.format(self.silences_file))

        if self.variants is not []:
            with open_utf8(self.variants_file, 'w') as out:
                for var in self.variants:
                    out.write(u" ".join(var) + u"\n")
            self.log.debug('writed {}'.format(self.variants_file))


    ############################################
    #
    # The above functions are abstracts and must be implemented by
    # child classes for each supported corpus.
    #
    ############################################

    name = NotImplemented
    """The name of the corpus"""

    phones = NotImplemented
    """A dict associating each phone in corpus with it's IPA symbol"""

    silences = []
    """A list of symbols for silence"""

    variants = []
    """A list of tonal variants associated with the phones"""

    def make_wavs(self):
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


class AbstractPreparatorWithCMU(AbstractPreparator):
    """Specialized wrapper for preparators relying on the CMU dictionary

    Abkhazia automatically downloaded the dictionary for you during
    installation. It is available for free at
    http://www.speech.cs.cmu.edu/cgi-bin/cmudict. The preparator is
    designed for version 0.7a of the CMU dictionary, but other recent
    versions could probably be used without changing anything.

    """
    default_cmu_dict = resource_filename(
        Requirement.parse('abkhazia'), 'abkhazia/share/cmudict.0.7a')

    def __init__(self, input_dir,
                 cmu_dict=None, output_dir=None, verbose=False):

        # call the AbstractPreparator __init__
        super(AbstractPreparatorWithCMU, self).__init__(
            input_dir, output_dir, verbose)

        # init path to CMU dictionary
        if cmu_dict is None:
            cmu_dict = self.default_cmu_dict

        if not os.path.isfile(cmu_dict):
            raise IOError(
                'CMU dictionary does not exist: {}'
                .format(cmu_dict))

        self.cmu_dict = cmu_dict
        self.log.debug('CMU dictionary is {}'.format(self.cmu_dict))
