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
"""Provides the CorpusSplit class"""

import ConfigParser
import random
import abkhazia.utils as utils


class CorpusSplit(object):
    """A class for spliting an abkhazia corpus into train and test subsets

    corpus : The abkhazia corpus to split. The corpus is assumed
      to be valid.

    output_dir : The output directory where to write the splits. The
      directory hierarchy 'output_dir'/{train, test}/data is
      created. The log file goes in
      'output_dir'/logs/split_corpus.log. By default use 'corpus_dir'

    random_seed : Seed for pseudo-random numbers generation
      (default is None and current system time is used)

    prune_lexicon: If True, remove from the lexicon all words that are
        not present at least once in the training set. This have
        effect on word-level language models. Could be useful when
        using a lexicon that is tailored to the corpus to the point of
        overfitting (i.e. only words occuring in the corpus were
        included and many other common words weren't), which could
        lead to overestimated performance on words from the lexicon
        appearing in the test only.

    verbose : This argument serves as initialization of the log2file
      module. See there for more documentation.

    """
    def __init__(self, corpus, log=utils.null_logger(), random_seed=None):
        self.log = log

        # seed the random generator
        if random_seed is not None:
            self.log.debug('random seed is %i', random_seed)
        random.seed(random_seed)

        # read utt2spk from the input corpus
        utt_ids, utt_speakers = self.corpus.utt2spk.items()
        self.utts = zip(utt_ids, utt_speakers)
        self.size = len(utt_ids)
        self.speakers = set(utt_speakers)
        self.log.debug('loaded %i utterances from %i speakers',
                       self.size, len(self.speakers))

    @staticmethod
    def default_test_prop():
        """Return the default proportion for the test set

        Try to read from configuration file, else return 0.5"""
        try:
            return float(utils.config.get(
                'split', 'default-test-proportion'))
        except ConfigParser.NoOptionError:
            return 0.5

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

        return (self.corpus.subcorpus(train_utt_ids),
                self.corpus.subcorpus(test_utt_ids))

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
        return self.split_from_speakers_list(speakers[:n_train_speakers])

    def split_from_speakers_list(self, train_speakers):
        """Split the corpus from a list of speakers in the train set

        Speakers in the list go in train set, other speakers go in
        testing set. Unregisterd speakers raise a RuntimeError.

        Return a pair (train, testing) of Corpus instances

        """

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

        return (self.corpus.subcorpus(train_utt_ids),
                self.corpus.subcorpus(test_utt_ids))

    def _proportions(self, test_prop, train_prop):
        """Return 'regularized' proportions of test and train data

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
