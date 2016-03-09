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
import shutil

from abkhazia import utils


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
    abstract preparator is prepare(). It converts the original data in
    'input_dir' to a corpus in the abkhazia format, storing the data
    in 'output_dir'

    """
    @classmethod
    def default_output_dir(cls):
        """Return the default output directory for corpus preparation

        This directory is 'data-directory'/'name', where
        'data-directory' is read from the abkhazia configuration file
        and 'name' is self.name

        """
        return os.path.join(
            utils.config.get('abkhazia', 'data-directory'),
            cls.name)

    @classmethod
    def default_input_dir(cls):
        """Return the input directory specified the conf file, or None"""
        try:
            name = cls.name.split('-')[0] + '-directory'
            res = utils.config.get('corpus', name)
            return None if res == '' else res
        except ConfigParser.NoOptionError:
            return None

    def __init__(self, input_dir, output_dir=None, verbose=False, njobs=1):
        # init njobs for parallelized preparation steps
        if not isinstance(njobs, int) or not njobs > 0:
            raise IOError('njobs must be a strictly positive integer')
        self.njobs = njobs

        # init input directory
        if not os.path.isdir(input_dir):
            raise IOError(
                'input directory does not exist:\n{}'.format(input_dir))
        self.input_dir = os.path.abspath(input_dir)

        # init output directory
        if output_dir is None:
            self.output_dir = self.default_output_dir()
        else:
            self.output_dir = os.path.abspath(output_dir)

        # create the log directory if not existing
        self.logs_dir = os.path.join(self.output_dir, 'logs')
        if not os.path.isdir(self.logs_dir):
            os.makedirs(self.logs_dir)

        # init the log
        self.verbose = verbose
        self.log = utils.get_log(
            os.path.join(self.logs_dir, 'data_preparation.log'), self.verbose)

        # init the directories output_dir/data/wavs
        self.data_dir = os.path.join(self.output_dir, 'data')
        self.wavs_dir = os.path.join(self.data_dir, 'wavs')

        # init output files that will be populated by prepare()
        def fname(name):
            """return complete filename"""
            return os.path.join(self.data_dir, name + '.txt')
        self.segments_file = fname('segments')
        self.speaker_file = fname('utt2spk')
        self.transcription_file = fname('text')
        self.lexicon_file = fname('lexicon')
        self.phones_file = fname('phones')
        self.variants_file = fname('variants')
        self.silences_file = fname('silences')

        self.log.debug('converting {} to abkhazia'.format(self.name))
        self.log.debug('reading from {}'.format(self.input_dir))

    def prepare(self):
        """Prepare the corpus from raw distribution to abkhazia format

        This method must not be overloaded in child classes as it
        ensure consistency with the abkhazia format.

        """
        self.log.info('writing to {}'.format(self.output_dir))

        # the successive preparation steps associated with the target
        # they will populate
        steps = [
            (self.make_segment, self.segments_file),
            (self.make_speaker, self.speaker_file),
            (self.make_transcription, self.transcription_file),
            (self.make_lexicon, self.lexicon_file),
            (self.make_phones, self.phones_file)
        ]

        # make_wavs has it own log message, run it separatly
        self.make_wavs()

        # run each step one after another
        for step, target in steps:
            self.log.info('preparing {}'.format(os.path.basename(target)))
            step()

    def broken_wav(self, wav):
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

    def prepare_wavs_dir(self, inputs, outputs):
        """Detect outputs already present and delete any undesired file"""
        self.log.debug('scanning {}...'.format(self.wavs_dir))

        target = dict((o, i) for i, o in zip(inputs, outputs))
        found = 0
        deleted = 0
        for wav in os.listdir(self.wavs_dir):
            # the complete path to the wav file
            path = os.path.join(self.wavs_dir, wav)

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

        To save some disk space, if the corpus audio file
        format is wav, the files will be linked and not copied.

        This method relies on self.list_audio_files() to get the input
        and output files.

        """
        # get the list of input and output files to prepare
        inputs, outputs = self.list_audio_files()

        self.log.info('preparing {} wav files'.format(len(inputs)))

        # should not occur, but if child class is badly implemented...
        if len(inputs) != len(outputs):
            raise ValueError('inputs and outputs must have the same size')

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

        # link or copy wav files in function of self.copy_wavs
        if self.audio_format == 'wav':
            action = (('copying', shutil.copy) if self.copy_wavs
                      else ('linking', os.symlink))

            self.log.debug('{} wav files...'.format(action[0]))
            for inp, out in zip(inputs, outputs):
                action[1](inp, out)
            self.log.debug('finished {} wavs'.format(action[0]))

        else:  # if original files are not wav, convert them
            self.log.info('converting {} {} files to wav...'
                          .format(len(inputs), self.audio_format))
            utils.wav.convert(inputs, outputs, self.audio_format, self.njobs,
                              verbose=5 if self.verbose else 1)
            self.log.debug('finished converting wavs')

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
        with utils.open_utf8(self.phones_file, 'w') as out:
            for phone in self.phones:
                out.write(u'{0} {1}\n'.format(phone, self.phones[phone]))
        self.log.debug('wrote {}'.format(self.phones_file))

        if self.silences is not []:
            with utils.open_utf8(self.silences_file, 'w') as out:
                for sil in self.silences:
                    out.write(sil + u"\n")
            self.log.debug('wrote {}'.format(self.silences_file))

        if self.variants is not []:
            with utils.open_utf8(self.variants_file, 'w') as out:
                for var in self.variants:
                    out.write(u" ".join(var) + u"\n")
            self.log.debug('wrote {}'.format(self.variants_file))

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

    # TODO this is actually a design error, we should have a decorator
    # or subclass instead
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
