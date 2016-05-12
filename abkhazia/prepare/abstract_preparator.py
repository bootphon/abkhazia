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

    def __init__(self, input_dir, log=utils.log2file.null_logger()):
        self.njobs = utils.default_njobs(local=True)
        self.log = log

        # init input directory
        if not os.path.isdir(input_dir):
            raise IOError(
                'input directory does not exist:\n{}'.format(input_dir))
        self.input_dir = os.path.abspath(input_dir)

        # init empty output corpus
        self.corpus = Corpus()

    def prepare(self, wavs_dir):
        """Prepare the corpus from raw distribution to abkhazia format

        This method must not be overloaded in child classes as it
        ensure consistency with the abkhazia format.

        """
        self.log.info('converting %s to abkhazia', self.name)
        self.log.debug('reading from %s', self.input_dir)

        c = self.corpus
        c.wavs = self.make_wavs(wavs_dir)
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

        wav : absolute path to a file in wavs_dir

        A wav file is broken if:
          - the file is empty
          - the file is a link and self.copy_wavs is True

        """
        if utils.is_empty_file(wav):
            return True
        if os.path.islink(wav) and self.copy_wavs:
            return True
        return False

    def _prepare_wavs_dir(self, wavs_dir, inputs, outputs):
        """Detect outputs already present and delete any undesired file"""
        self.log.debug('scanning %s', wavs_dir)

        target = dict((o, i) for i, o in zip(inputs, outputs))
        found = 0
        deleted = 0
        for wav in os.listdir(wavs_dir):
            # the complete path to the wav file
            path = os.path.realpath(os.path.join(wavs_dir, wav))

            # the target file is found in the directory, delete it if
            # it is empty, delete it it's a link and we force copying
            if wav in target and not self._broken_wav(path):
                del target[wav]
                found += 1
            else:
                utils.remove(path)
                deleted += 1

        self.log.debug(
            'found %s files, deleted %s undesired files', found, deleted)

        # return the updated inputs and outputs
        return target.values(), target.keys()

    def make_wavs(self, wavs_dir):
        """Convert to wav and copy/link the corpus audio files

        Because converting thousands of files can be heavy, only the
        files that are not already present in wavs_dir are
        converted.

        Moreover any file present in wavs_dir but not listed as a
        desired wav file will be deleted.

        To save some disk space, if the corpus audio file format is
        wav, the files will be linked and not copied (except if
        self.copy_wavs is True).

        This method relies on self.list_audio_files() to get the input
        and output files.

        """
        # get the list of input and output files to prepare
        inputs = []
        outputs = []
        for f in self.list_audio_files():
            try:  # we have a pair: rename the audio file
                i, o = f
            except ValueError:  # not renamed
                i = f
                o = os.path.splitext(os.path.basename(f))[0] + '.wav'
            inputs.append(i)
            outputs.append(o)

        self.log.info('preparing %s wav files', len(inputs))

        if os.path.isdir(wavs_dir):
            # the wavs directory already exists, clean it and prepare
            # it for copy/link of wav files
            inputs, outputs = self._prepare_wavs_dir(wavs_dir, inputs, outputs)
        else:  # wavs_dir does not exist
            os.makedirs(wavs_dir)

        # the job is done if all the files are already here, else
        # we continue the preparation
        if len(inputs) == 0:
            self.log.debug(
                'all wav files already present in the directory')
        else:
            # append path to the directory in outputs
            outputs = [os.path.join(wavs_dir, out) for out in outputs]

            # If original files are not wav, convert them. Else link or
            # copy wav files in function of self.copy_wavs. The wavs that
            # are not at 16 kHz are resampled.
            self.log.debug('converting %s %s files to 16kHz mono wav...',
                           len(inputs), self.audio_format)
            utils.wav.convert(
                inputs, outputs, self.audio_format,
                self.njobs, verbose=5, copy=self.copy_wavs)
            self.log.debug('finished converting wavs')

        # finally build the corpus wavs dictionary
        return {os.path.splitext(os.path.basename(w))[0]: w
                for w in utils.list_files_with_extension(
                        wavs_dir, '.wav', abspath=True, realpath=False)}

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
        """Return a list of audio files belonging to the corpus

        If the returned list is composed of pairs of str, it is
        interpreted as (input, output) names of the audio files.  If
        the returned list is composed of str, it is (input) and the
        files are not renamed.

        (input) must be an absolute real path (with links resolved).
        If specified (output) must be a basename with '.wav' extension

        This method is used by self.make_wavs().

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

    def __init__(self, input_dir, cmu_dict=None, log=utils.null_logger()):
        super(AbstractPreparatorWithCMU, self).__init__(input_dir, log)

        # init path to CMU dictionary
        if cmu_dict is None:
            cmu_dict = self.default_cmu_dict
        if not os.path.isfile(cmu_dict):
            raise IOError(
                'CMU dictionary does not exist: {}'
                .format(cmu_dict))

        self.cmu_dict = cmu_dict
        self.log.debug('CMU dictionary is %s', self.cmu_dict)
