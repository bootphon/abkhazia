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
"""Provides the CorpusSplit class"""

import ConfigParser
import random
from abkhazia.utils import logger, config


class CorpusSplit(object):
    """A class for spliting an abkhazia corpus into train and test subsets

    corpus : The abkhazia corpus to split. The corpus is assumed
      to be valid.

    log : a logging.Logger instance to send log messages

    random_seed : Seed for pseudo-random numbers generation (default
      is to use the current system time)

    prune : If True the train and testing corpora are pruned (default is True)

    In the split and split_by_speakers methods, arguments are as follow:

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
    def __init__(self, corpus, log=logger.null_logger(),
                 random_seed=None, prune=True):
        self.log = log
        self.prune = prune
        self.corpus = corpus

        # seed the random generator
        if random_seed is not None:
            self.log.debug('random seed is %i', random_seed)
        random.seed(random_seed)

        # read utt2spk from the input corpus
        utt_ids, utt_speakers = zip(*self.corpus.utt2spk.iteritems())
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
            return float(config.get(
                'split', 'default-test-proportion'))
        except ConfigParser.NoOptionError:
            return 0.5

    def split(self, train_prop=None, test_prop=None):
        """Split the corpus by utterances regardless of the speakers

        Both generated subsets get speech from all the speakers with a
        number of utterances by speaker in each set matching the
        number of utterances by speaker in the whole corpus.

        We can have train_prop + test_prop < 1, in that case part of
        the source corpus is ignored.

        Return a pair (train, testing) of Corpus instances

        """
        train_prop, test_prop = self._proportions(train_prop, test_prop)

        train_utt_ids = []
        test_utt_ids = []
        for speaker in self.speakers:
            spk_utts = [utt_id for utt_id, utt_speaker in self.utts
                        if utt_speaker == speaker]

            # if len(spk_utts) <= 1:
            #     self.log.warning(
            #         'speaker {} has only {} sentence'
            #         .format(speaker, len(spk_utts)))

            n_train = int(round(len(spk_utts) * train_prop))
            n_test = int(round(len(spk_utts) * test_prop))

            self.log.debug(
                'spliting %i utterances from speaker %s -> '
                '%i for train, %i for test',
                len(spk_utts), speaker, n_train, n_test)

            # sample train and test utterances at random for this speaker
            random.shuffle(spk_utts)
            train_utts = spk_utts[:n_train]
            test_utts = spk_utts[n_train:n_train + n_test]

            # add to train and test sets
            train_utt_ids += train_utts
            test_utt_ids += test_utts

        return (self.corpus.subcorpus(train_utt_ids, prune=self.prune),
                self.corpus.subcorpus(test_utt_ids, prune=self.prune))

    def split_by_speakers(self, train_prop=None, test_prop=None):
        """Split the corpus by speakers

        Generated train and test subsets get speech from different
        speakers and the data for each speaker is attributed to one of
        the two sets as a whole.

        Note that this might not be appropriate when the amount of
        utterances available per speaker is too unbalanced.

        Return a pair (train, testing) of Corpus instances

        """
        train_prop, test_prop = self._proportions(train_prop, test_prop)

        # randomize the speakers
        speakers = list(self.speakers)
        random.shuffle(speakers)

        # split from a subpart of the randomized speakers
        n_train = int(round(train_prop * len(self.speakers)))
        n_test = int(round(test_prop * len(self.speakers)))
        return self.split_from_speakers_list(
            speakers[:n_train],
            speakers[n_train:n_train + n_test])

    def split_from_speakers_list(self, train_speakers, test_speakers):
        """Split the corpus from a list of speakers in the train set

        Speakers in the list go in train set, test speakers go in
        testing set. Unregistered speakers raise a RuntimeError.

        Return a pair (train, testing) of Corpus instances

        """
        # assert we have no unknown speakers
        for speakers, message in (
                (train_speakers, 'train_speakers'),
                (train_speakers, 'train_speakers')):
            unknown = [spk for spk in speakers if spk not in self.speakers]
            if unknown != []:
                raise RuntimeError(
                    "The following speakers specified in {} "
                    "are not found in the corpus: {}".format(message, unknown))

        train_utt_ids = []
        test_utt_ids = []
        for speaker in self.speakers:
            spk_utts = [utt_id for utt_id, utt_speaker in self.utts
                        if utt_speaker == speaker]

            if speaker in train_speakers:
                train_utt_ids += spk_utts
                msg = 'train'
            elif speaker in test_speakers:
                test_utt_ids += spk_utts
                msg = 'test'
            else:
                msg = None

            if msg:
                self.log.debug(
                    '%i utterances from speaker %s -> %s',
                    len(spk_utts), speaker, msg)

        return (self.corpus.subcorpus(train_utt_ids, prune=self.prune),
                self.corpus.subcorpus(test_utt_ids, prune=self.prune))

    def _proportions(self, train_prop, test_prop):
        """Return 'regularized' proportions of test and train data

        Return the tuple (test_prop, train_prop), ensures they are in
        [0, 1] and their sum is below or equal to 1. If None, return
        the default values.

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

        if test_prop + train_prop > 1:
            raise RuntimeError(
                'sum of test and train proportion is > 1')

        return train_prop, test_prop
