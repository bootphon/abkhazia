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
"""Provides the CorpusFilter class"""

import ConfigParser
import random
import matplotlib.pyplot as plt
import numpy as np

from collections import defaultdict
from operator import itemgetter
from math import exp
from abkhazia.utils import logger, config


class CorpusFilter(object):
    """A class for Filtering the distribution of speech duration 
    over an Abkhazia corpus.

    corpus : The abkhazia corpus to filter. The corpus is assumed
      to be valid.

    log : A logging.Logger instance to send log messages

    random_seed : Seed for pseudo-random numbers generation (default
      is to use the current system time)

    function : A string that specifies the cutting function that
      will be used on the corpus

    plot : A boolean which, if set to true, enables the plotting
      of the speech distribution and the cutting function
    """
    def __init__(self, corpus, log=logger.null_logger(),
                 random_seed=None):
        self.log = log
        self.corpus = corpus

        # read utt2spk from the input corpus
        utt_ids, utt_speakers = zip(*self.corpus.utt2spk.iteritems())
        self.utts = zip(utt_ids, utt_speakers)
        self.size = len(utt_ids)
        self.speakers = set(utt_speakers)
        self.limits = dict()
        self.spk2utts = dict()
        self.utt2dur=self.corpus.utt2duration()
        self.log.debug('loaded %i utterances from %i speakers',
                       self.size, len(self.speakers))

    def create_filter(self,function,nb_speaker=None,plot=True):
        """Prepare the corpus for the cutting
        
        The speakers are sorted by their speech duration. 
        A cutting function is then computed with the function specified in input
        
        If plot=True, a plot of the speech duration distribution and of the cutting
        function will be displayed.
        """
        utt2dur = self.utt2dur
        spk2dur=dict()
        speakers=self.speakers
        spk2utts=self.spk2utts
        utts=self.utts

        self.log.info('sorting speaker by the total duration of speech')

        # Sort the utterances in order of appearance in the wave file 
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

        # Sort Speech duration from longest to shortest
        sorted_speaker=sorted(spk2dur.iteritems(), key=lambda(k,v):(v,k))
        sorted_speaker.reverse()
        if nb_speaker:
            if nb_speaker<1 or nb_speaker>len(sorted_speaker):
                self.log.info('Invalid number of speaker, keeping all speakers')
                nb_speaker=len(sorted_speaker)
            sorted_speaker=sorted_speaker[0:nb_speaker]
            
 
        # Plot the Speech duration distribution, and superimpose a power law
        names=[spk_id for (spk_id,duration) in sorted_speaker]
        times=[duration for (spk_id,duration) in sorted_speaker]
        times_reduced=[format(u0,'.1f') for u0 in times]
        total=self.corpus.duration(format='seconds')
        self.log.debug('corpus.duration=%i, sum(sorted_speaker)=%i',total/60,sum(times)/60)
        (spk_id0,duration0)=sorted_speaker[0]
        x_axis=range(1,1+len(names))
        plt.bar(x_axis,times,width=0.7,align="center",alpha=0.7,label="speech time")

        # Compute the distribution used to cut the corpus
        if function == "exponential":
            distrib=[duration0*exp(-0.4*(ind-1)) for ind in x_axis]
        elif function =="power-law":
            exponent=1
            distrib=[duration0/((ind)**exponent)+30 for ind in x_axis]
        elif function =="step":
            #number of speaker for which we keep the whole speech
            spk_threshold=5 
            
            #duration of speech we keep for the other speakers : 
            dur_threshold=10*60
            distrib=times[0:spk_threshold]
            distrib[spk_threshold+1:len(times)]=[dur_threshold] *(len(times)-spk_threshold)
            
        distrib_reduced=[format(u0,'.1f') for u0 in distrib]
        plt.scatter(x_axis,distrib,marker='*',color='r',
                    label="power law distribution (in minutes)")
            
        for i,txt in enumerate(distrib_reduced):
            plt.annotate(txt,(x_axis[i],distrib[i]+2),rotation=45,)
        self.log.info('for %i speakers, the filter gives %i minutes of speech',
                    len(sorted_speaker),sum(distrib)/60)

        self.limits=dict(zip(names,distrib))
        
        
        # Show Plot
        for j,txt in enumerate(times_reduced):
            if j!=0:
                plt.annotate(txt,(x_axis[j],times[j]+3),rotation=45)
        self.log.info('Speech duration for corpus : %i minutes',sum(times)/60)
        if plot==True:
            plt.legend() 
            plt.xticks(x_axis,names,rotation=45)
            plt.xlabel('speaker')
            plt.ylabel('duration (in minutes)',rotation=90)
        
            plt.show()

        return(self.filter_corpus(names,function))

    def filter_corpus(self,names,function):
        """Cut the corpus according to the cutting function specified
        
        Return the subcorpus 
        """
        limits=self.limits
        time=0
        utt_ids=[]
        spk2utts=self.spk2utts
        utt2dur=self.utt2dur
        not_kept_utts=defaultdict(list)
        corpus=self.corpus
        
        # create list of utterances we want to keep, utterances we don't want to keep
        for speaker in names:
            utt_and_dur=zip(spk2utts[speaker],[utt2dur[utt] for utt in spk2utts[speaker]])
            decreasing_utts=sorted(utt_and_dur,key=lambda utt_and_dur: utt_and_dur[1],reverse=True)
            ascending_utts=sorted(utt_and_dur,key=lambda utt_and_dur: utt_and_dur[1])

            nb_utt=0
            for utts in spk2utts[speaker]:
                time+=utt2dur[utts]
                if time<limits[speaker] or nb_utt<10:
                    utt_ids.append(utts)
                    nb_utt=nb_utt+1 
                else:
                    #print speaker,time,limits[speaker],nb_utt
                    nb_utt=0;
                    time=0;
                    break

                
            kept_utt_set=set(utt_ids)
             
            # here we build the list of utts we remove, and we adjust the boundaries of
            # the other utterancess, in order to have correct timestamps
            
            for utt in spk2utts[speaker]:
                #for each wav, we compute the cumsum of the lengths of the utts we remove
                # in order to have correct timestamps for the other utts in the files
                offset=0
                wav_id,utt_tbegin,utt_tend=corpus.segments[utt]
                corpus.segments[utt]=(wav_id,utt_tbegin-offset,utt_tend-offset)
                if utt_tbegin-offset<0 or utt_tend-offset<0:
                    self.log.info('WARN : offset is greater than utterance boundaries')
                if utt not in kept_utt_set:
                    offset=offset+utt2dur[utt]
                    not_kept_utts[speaker].append((utt,corpus.segments[utt]))

        return(self.corpus.subcorpus(utt_ids,prune=True,name=function,validate=True),
                not_kept_utts);
