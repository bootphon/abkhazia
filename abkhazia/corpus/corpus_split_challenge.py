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
import os
from collections import defaultdict
from abkhazia.utils import logger, config


class CorpusSplitChallenge(object):
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


    def splitChallenge(self,nb_new_spkr, test_dur=10,out=''):
        """Split the corpus by utterances regardless of the speakers

        Both generated subsets get speech from all the speakers with a
        number of utterances by speaker in each set matching the
        number of utterances by speaker in the whole corpus.

        Return a pair (train, testing) of Corpus instances

        """
        utt2dur=self.corpus.utt2duration()
        utts=self.utts
        speakers=self.speakers
        spk2utts=dict()
        spk2dur=dict()
        # Select n "new" speaker for the test part
        spk2utts_temp=defaultdict(list)
        for utt,spkr in utts:
            utt_start=self.corpus.segments[utt][1]
            spk2utts_temp[spkr].append([utt,utt_start])
        for spkr in speakers:
            spk2utts_temp[spkr]=sorted(spk2utts_temp[spkr], key=lambda x: x[1])
            spk2utts[spkr]=[utt for utt,utt_start in spk2utts_temp[spkr]]
            duration=sum([utt2dur[utt_id] for utt_id in spk2utts[spkr]])
            spk2dur[spkr]=duration
 
        self.spk2utts=spk2utts
        sorted_speaker=sorted(spk2dur.iteritems(), key=lambda(k,v):(v,k))
        new_speakers=set([spkr for spkr,duration in sorted_speaker[0:nb_new_spkr]]) 
        
        ## Add males to the new speakers in THCHS30 ##
        if 'C08' not in new_speakers:
            new_speakers.add('C08')
        if 'D08' not in new_speakers:
            new_speakers.add('D08')
        noisy=set(['A05','C22','C14','D32','A23','A36','D31','B11'])

        train_utt_ids = []
        test_utt_ids = []

        # Split the corpus in test/train, to have test_dur min
        # of speech in the test set
        for spkr in speakers:
            if spkr in noisy :
                continue
            spk_utts = [utt_id for utt_id, utt_speaker in self.utts
                        if utt_speaker == spkr]

            # sample utterances at random for this speaker 
            test_utts_temp = random.sample(spk_utts, len(spk_utts))
            time=0
            utts=enumerate(test_utts_temp)

            # while the total of speech for this speaker is not 10 minutes,
            # add a randomly picked utt in the test set
            test_utts=[]
            while (time<10):
                try : 
                    utt_ind,utt_id=next(utts)
                except StopIteration :
                    break
                time=time+(utt2dur[utt_id]/60)
                test_utts.append(utt_id)

            test_set=set(test_utts)
            if spkr not in new_speakers:
                train_utts=[utt_id for utt_id in spk_utts if utt_id not in test_set]
            else:
                train_utts=[]
            # add to train and test sets
            train_utt_ids += train_utts
            test_utt_ids += test_utts

        self.write_new_speakers_set(new_speakers,out)
        return (self.corpus.subcorpus(train_utt_ids, prune=self.prune),
                self.corpus.subcorpus(test_utt_ids, prune=self.prune),new_speakers)

    def write_new_speakers_set(self,new_speakers,out):
        if not os.path.isdir(out):
            os.makedirs(out)
        out_path=os.path.join(out,'new_speakers.txt')
        new_speakers_list=list(new_speakers)

        with open(out_path,'w') as outf:
            for spkr in new_speakers_list:
                outf.write(u'{}\n'.format(spkr))




        
