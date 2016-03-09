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
"""Provides a class to split an abkhazia corpus in train and test subsets"""

import ConfigParser
import os
import random
import shutil

import abkhazia.utils as utils
import abkhazia.utils.basic_io as io


class SplitCorpus(object):
    """A class for spliting an abkhazia corpus into train and test subsets

    corpus_dir : The root directory of the abkhazia corpus to
      split. This directory must contain a validated abkhazia corpus.

    output_dir : The output directory where to write the splits. The
      directory 'output_dir'/split is created, with two subdirs (test
      and train). The log file goes in
      'output_dir'/logs/split_corpus.log. By default use 'corpus_dir'

    random_seed : Seed for pseudo-random numbers generation
      (default is None and current system time is used)

    verbose : This argument serves as initialization of the log2file
      module. See there for more documentation.

    """
    @staticmethod
    def default_test_prop():
        """Return the default proportion for the test set

        Try to read from configuration file, else return 0.5"""
        try:
            return float(utils.config.get(
                'split', 'default-test-proportion'))
        except ConfigParser.NoOptionError:
            return 0.5

    def __init__(self, corpus_dir, output_dir=None,
                 random_seed=None, verbose=False):
        # init the corpus directory
        if not os.path.isdir(corpus_dir):
            raise OSError('{} is not a directory'.format(corpus_dir))
        self.data_dir = os.path.join(corpus_dir, 'data')
        if not os.path.isdir(self.data_dir):
            raise OSError('{} is not a directory'.format(self.data_dir))

        # all we need from the corpus is the utt2spk.txt file
        utt2spk_file = os.path.join(self.data_dir, 'utt2spk.txt')
        if not os.path.exists(utt2spk_file):
            raise OSError('{} file does not exist'.format(utt2spk_file))

        # init the output directory
        if output_dir is None:
            output_dir = corpus_dir
        split_dir = os.path.join(output_dir, 'split')
        if os.path.exists(split_dir):
            raise OSError(
                'output split directory alreary existing: {}'
                .format(split_dir))

        # init output_dir/{test, train}
        self.test_dir = os.path.join(output_dir, 'split', 'test')
        self.train_dir = os.path.join(output_dir, 'split', 'train')
        for path in (self.test_dir, self.train_dir):
            if not os.path.exists(path):
                os.makedirs(path)

        # init the log system
        self.log = utils.log2file.get_log(
            os.path.join(output_dir, 'logs', 'split_corpus.log'), verbose)

        # seed the random generator
        if random_seed is not None:
            self.log.debug('random seed is %i', random_seed)
        random.seed(random_seed)

        # read the utt2spk file from the input corpus
        self.log.info('reading from %s', utt2spk_file)
        utt_ids, utt_speakers = io.read_utt2spk(utt2spk_file)
        self.utts = zip(utt_ids, utt_speakers)
        self.size = len(utt_ids)
        self.speakers = set(utt_speakers)
        self.log.debug('loaded %i utterances from %i speakers',
                       self.size, len(self.speakers))

    def _write(self, train_utt_ids, test_utt_ids):
        """Write the train and test split corpus to the output directory

        Before writing the files, this finction also sort them (with
        respect to the first comulmn)

        """
        self.log.info(
            'splitting proportions are %f for train and %f for test',
            round(float(len(train_utt_ids))/self.size, 3),
            round(float(len(test_utt_ids))/self.size, 3))

        self.log.info(
            'writing to %s',
            os.path.abspath(os.path.join(self.test_dir, '..')))

        # for train and test subsets
        for target_dir, utts in [(self.train_dir, train_utt_ids),
                                 (self.test_dir, test_utt_ids)]:
            # take subparts of utt2spk.txt, text.txt and segments.txt
            for filein in (['utt2spk.txt', 'text.txt', 'segments.txt']):
                target = os.path.join(target_dir, filein)
                try:
                    self.log.debug('writing %s', target)
                    io.copy_first_col_matches(
                        os.path.join(self.data_dir, filein),
                        target, utts)
                    io.cpp_sort(target)
                except (OSError, ValueError):
                    try:
                        utils.remove(target)
                    except shutil.Error:
                        self.log.error("can't delete %s", self.train_dir)
                    finally:
                        raise OSError('cannot writing to {}'.format(target))

    def _proportions(self, test_prop, train_prop):
        """Return 'regularized' proprotions of test and train data

        Return the tuple (test_prop, train_prop), ensures they are in
        [0, 1] and their sum is 1. If None, return the default values.

        """
        # set default proportion values
        if test_prop is None:
            test_prop = (self.default_test_prop
                         if train_prop is None else 1 - train_prop)
        if train_prop is None:
            train_prop = 1 - test_prop

        if test_prop < 0 or test_prop > 1:
            raise RuntimeError('test proportion must be in [0, 1]')
        if train_prop < 0 or train_prop > 1:
            raise RuntimeError('train proportion must be in [0, 1]')

        self.log.debug('proportion for train is %f', train_prop)
        self.log.debug('proportion for test is %f', test_prop)

        if test_prop + train_prop != 1:
            raise RuntimeError(
                'sum of test and train proportion is not 1')

        return test_prop, train_prop

    def split(self, test_prop=None, train_prop=None):
        """Split the corpus by utterances regardless of the speakers

        Both generated subsets get speech from all the speakers with a
        number of utterances by speaker in each set matching the
        number of utterances by speaker in the whole corpus.

        test_prop : float, should be between 0.0 and 1.0 and
          represent the proportion of the dataset to include in the
          test split. If None, the value is automatically set to the
          complement of the train size. If train size is also None,
          test size is set to 0.5. (default is None)

        train_prop : float, should be between 0.0 and 1.0 and
          represent the proportion of the dataset to include in the
          train split. If None, the value is automatically set to the
          complement of the test size. (default is None)

        """
        test_prop, train_prop = self._proportions(test_prop, train_prop)

        train_utt_ids = []
        test_utt_ids = []
        for speaker in self.speakers:
            spk_utts = [utt_id for utt_id, utt_speaker in self.utts
                        if utt_speaker == speaker]

            if len(spk_utts) <= 1:
                raise RuntimeError(
                    'Speaker {} has only {} sentence'
                    .format(speaker, len(spk_utts)))

            n_train = int(round(len(spk_utts) * train_prop))

            self.log.debug(
                'spliting %i utterances from speaker %s -> '
                '%i for train, %i for test',
                len(spk_utts), speaker, n_train, len(spk_utts) - n_train)

            # sample train and test utterances at random for this speaker
            train_utts = random.sample(spk_utts, n_train)
            test_utts = list(set.difference(set(spk_utts), set(train_utts)))

            # add to train and test sets
            train_utt_ids += train_utts
            test_utt_ids += test_utts

        self._write(train_utt_ids, test_utt_ids)

    def split_by_speakers(self, test_prop=None, train_prop=None):
        """Split the corpus by speakers

        Generated train and test subsets get speech from different
        speakers and the data for each speaker is attributed to one of
        the two sets as a whole.

        Note that this might not be appropriate when the amount of
        utterances available per speaker is too unbalanced.

        test_prop : If float, should be between 0.0 and 1.0 and
          represent the proportion of the dataset to include in the
          test split. If int, represents the absolute number of test
          samples. If None, the value is automatically set to the
          complement of the train size. If train size is also None,
          test size is set to 0.5. (default is None)

        train_prop : If float, should be between 0.0 and 1.0 and
          represent the proportion of the dataset to include in the
          train split. If int, represents the absolute number of train
          samples. If None, the value is automatically set to the
          complement of the test size. (default is None)

        """
        test_prop, train_prop = self._proportions(test_prop, train_prop)

        # randomize the speakers
        speakers = list(self.speakers)
        random.shuffle(speakers)

        # split from a subpart of the randomized speakers
        n_train_speakers = int(round(train_prop * len(self.speakers)))
        self.split_from_speakers_list(speakers[:n_train_speakers])

    def split_from_speakers_list(self, train_speakers):
        """Split the corpus from a list of speakers in the train set"""

        unknown = [spk for spk in train_speakers if spk not in self.speakers]
        if unknown != []:
            raise RuntimeError(
                "The following speakers specified in train_speakers "
                "are not found in the corpus: {}".format(unknown))

        train_utt_ids = []
        test_utt_ids = []
        for speaker in self.speakers:
            spk_utts = [utt_id for utt_id, utt_speaker in self.utts
                        if utt_speaker == speaker]

            if speaker in train_speakers:
                train_utt_ids += spk_utts
                msg = 'train'
            else:
                test_utt_ids += spk_utts
                msg = 'test'
            self.log.debug(
                '%i utterances from speaker %s -> %s',
                len(spk_utts), speaker, msg)

        self._write(train_utt_ids, test_utt_ids)
