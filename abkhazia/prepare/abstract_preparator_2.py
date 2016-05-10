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
"""Provides a base class for corpus preparation in the abkhazia format"""

import ConfigParser
import os
import pkg_resources

from abkhazia import utils
from abkhazia.core.corpus import Corpus


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

    'verbose' : If True, send all log messages to stdout, if False
       send only info messages and above. See the log2file module for
       more details.

    Methods
    -------

    From a user perspective, the most important methods offered by the
    abstract preparator is prepare(). It converts the original data in
    'input_dir' to a corpus in the abkhazia format, storing the data
    in 'output_dir'.

    """
    @classmethod
    def default_input_dir(cls):
        """Return the input directory specified the conf file, or None"""
        try:
            name = cls.name.split('-')[0] + '-directory'
            res = utils.config.get('corpus', name)
            return None if res == '' else res
        except ConfigParser.NoOptionError:
            return None

    def __init__(self, input_dir, verbose=False, njobs=1):
        # init njobs for parallelized preparation steps
        if not isinstance(njobs, int) or not njobs > 0:
            raise IOError('njobs must be a strictly positive integer')
        self.njobs = njobs

        # init input directory
        if not os.path.isdir(input_dir):
            raise IOError(
                'input directory does not exist:\n{}'.format(input_dir))
        self.input_dir = os.path.abspath(input_dir)

        # init empty output corpus
        self.corpus = Corpus()

        # init the directories output_dir/data/wavs
        self.data_dir = os.path.join(self.output_dir, 'data')
        self.wavs_dir = os.path.join(self.data_dir, 'wavs')

        # init the log
        self.verbose = verbose
        self.log = utils.get_log(
            os.path.join(self.data_dir, 'corpus_preparation.log'),
            self.verbose)

    def prepare(self):
        """Prepare the corpus from raw distribution to abkhazia format

        This method must not be overloaded in child classes as it
        ensure consistency with the abkhazia format.

        """
        self.log.debug('converting {} to abkhazia'.format(self.name))
        self.log.debug('reading from {}'.format(self.input_dir))

        c = self.corpus
        c.wavs = self.make_wavs()
        c.segments = self.make_segment()
        c.lexicon = self.make_lexicon()
        c.text = self.make_transcription()
        c.utt2spk = self.make_speaker()
        c.phones = self.phones
        c.silences = self.silences
        c.variants = self.variants

        return c

    def _broken_wav(self, wav):
        """Return True if the wav needs to be copied again

        wav : absolute path to a file in self.wavs_dir

        A wav file is broken if:
          - the file is empty
          - the file is a link and self.copy_wavs is True

        """
        if utils.is_empty_file(wav):
            return True
        if os.path.islink(wav) and self.copy_wavs:
            return True
        return False

    def _prepare_wavs_dir(self, inputs, outputs):
        """Detect outputs already present and delete any undesired file"""
        self.log.debug('scanning {}...'.format(self.wavs_dir))

        target = dict((o, i) for i, o in zip(inputs, outputs))
        found = 0
        deleted = 0
        for wav in os.listdir(self.wavs_dir):
            # the complete path to the wav file
            path = os.path.realpath(os.path.join(self.wavs_dir, wav))

            # the target file is found in the directory, delete it if
            # it is empty, delete it it's a link and we force copying
            if wav in target and not self.broken_wav(path):
                del target[wav]
                found += 1
            else:
                utils.remove(path)
                deleted += 1

        self.log.debug('found {} files, deleted {} undesired files'
                       .format(found, deleted))

        # return the updated inputs and outputs
        return target.values(), target.keys()

    def make_wavs(self):
        """Convert to wav and copy the corpus audio files

        Because converting thousands of files can be heavy, only the
        files that are not already present in self.output_dir are
        converted.

        Moreover any file present in output_dir but not listed as a
        desired wav file will be deleted.

        To save some disk space, if the corpus audio file format is
        wav, the files will be linked and not copied (except if
        self.copy_wavs is True).

        This method relies on self.list_audio_files() to get the input
        and output files.

        """
        # get the list of input and output files to prepare
        inputs, outputs = self.list_audio_files()
        self.log.info('preparing {} wav files'.format(len(inputs)))

        # should not occur, except if child class is badly implemented
        if len(inputs) != len(outputs):
            raise ValueError(
                'number of audio inputs and outputs must be equal')

        if os.path.isdir(self.wavs_dir):
            # the wavs directory already exists, clean and prepare for copy
            inputs, outputs = self.prepare_wavs_dir(inputs, outputs)

            # the job is done if all the files are already here, else
            # we continue the preparation
            if len(inputs) == 0:
                self.log.debug(
                    'all wav files already present in the directory')
                return
        else:  # self.wavs_dir does not exist
            os.makedirs(self.wavs_dir)

        # append path to the directory in outputs
        outputs = [os.path.join(self.wavs_dir, o) for o in outputs]

        # If original files are not wav, convert them. Else link or
        # copy wav files in function of self.copy_wavs. The wavs that
        # are not at 16 kHz are resampled.
        self.log.debug('converting {} {} files to 16kHz mono wav...'
                       .format(len(inputs), self.audio_format))
        utils.wav.convert(
            inputs, outputs, self.audio_format, self.njobs,
            verbose=5 if self.verbose else 0, copy=self.copy_wavs)
        self.log.debug('finished converting wavs')

    ############################################
    #
    # The above functions are abstracts and must be implemented by
    # child classes for each supported corpus.
    #
    ############################################

    name = NotImplemented
    """The name of the corpus"""

    description = NotImplemented
    """A one line description of the corpus"""

    audio_format = NotImplemented
    """The format of audio files in the corpus

    This format must be 'wav' or a format supported by the
    abkhazia.utils.convert2wav.convert function.

    """

    copy_wavs = False
    """A boolean used only for corpora with original audio files in wav

    By default abkhazia will link wav files, setting this to True will
    force copy. Used in the make_wavs() method.

    """

    phones = NotImplemented
    """A dict associating each phone in corpus with it's IPA symbol"""

    silences = []
    """A list of symbols for silence"""

    variants = []
    """A list of tonal variants associated with the phones"""

    def list_audio_files(self):
        """Return a tuple (inputs, outputs) of two lists of audio files

        'inputs' is the list of audio files to convert to
            abkhazia. Filenames in the list must be absolute paths.

        'outputs' is the list of target files to create in
            'self.wavs_dir'. Filenames in the list must be only
            basenames (ie pure filenames with no path).

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
    default_cmu_dict = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('abkhazia'),
        'abkhazia/share/cmudict.0.7a')

    def __init__(self, input_dir, cmu_dict=None,
                 output_dir=None, verbose=False, njobs=1):
        # call the AbstractPreparator __init__
        super(AbstractPreparatorWithCMU, self).__init__(
            input_dir, output_dir, verbose, njobs)

        # init path to CMU dictionary
        if cmu_dict is None:
            cmu_dict = self.default_cmu_dict

        if not os.path.isfile(cmu_dict):
            raise IOError(
                'CMU dictionary does not exist: {}'
                .format(cmu_dict))

        self.cmu_dict = cmu_dict
        self.log.debug('CMU dictionary is {}'.format(self.cmu_dict))