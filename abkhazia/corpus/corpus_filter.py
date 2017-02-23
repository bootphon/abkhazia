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
import seaborn as sns
import os


from collections import defaultdict
from operator import itemgetter
from math import exp
from abkhazia.utils import logger, config, open_utf8


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
    # For the THCHS30 corpus, select 150 utt from each text (A, 
    # B, C, D), from 2 males and 2 females, and 2x50 utterances
    # from each text, from 4 males and 4 females
    THCHS30_family = ['A08', 'B08', 'C04', 'D21']
    THCHS30_outsiders1 = ['A33', 'B06', 'C08', 'D08']
    THCHS30_outsiders2 = ['A36', 'B02', 'C19', 'D07']
    limit = {'A': 100, 'B' : 350, 'C' : 600, 'D' : 850}
     
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
        self.gender = dict()
        self.spk2utts = dict()
        self.utt2dur=self.corpus.utt2duration()
        self.log.debug('loaded %i utterances from %i speakers',
                       self.size, len(self.speakers))

    def create_filter(self,out_path,function,
            nb_speaker=None,plot=True,new_speakers=10,THCHS30=False):
        """Prepare the corpus for the cutting
        
        The speakers are sorted by their speech duration. 
        A cutting function is then computed with the function specified in input
        
        If plot=True, a plot of the speech duration distribution and of the cutting
        function will be displayed.
        """
        utt2dur = self.utt2dur
        spk2dur=dict()
        speakers=self.speakers
        segments=self.corpus.segments
        spk2utts=self.spk2utts
        utts=self.utts

        self.log.info('sorting speaker by the total duration of speech')

        # Sort the utterances in order of appearance in the wave file 
        spk2utts_temp=defaultdict(list)
        for utt,spkr in utts:
            utt_start=segments[utt][1]
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



        # For the THCHS30 corpus, force the speaker selection and 
        # put color to the gender : 
        males_to_keep = set(['A08','B08'])
        #male = set(['A08','B08','C08','D08','A33','B21','A09','B34','A35','A05'])
        noisy = set(['A05','C22','C14','D32','A23','A36','D31','B11'])

        # For the LibriSpeech corpus, read SPEAKER.TXT to find the genders :
        #male=set()
        #self.librispeech_gender(path='/home/julien/workspace/data/librispeech-raw/LibriSpeech/SPEAKERS.TXT')
        #for speaker in speakers:
        #    try:
        #        self.gender[speaker]
        #    except:
        #        continue
        #    if self.gender[speaker]=='M':
        #        male.add(speaker)


        #nb_speaker=90

        if nb_speaker:
            if nb_speaker<1 or nb_speaker>len(sorted_speaker):
                self.log.info('Invalid number of speaker, keeping all speakers')
                nb_speaker=len(sorted_speaker)
            sorted_speaker=sorted_speaker[0:nb_speaker]

        
        ### For the THCHS30 corpus, force the selection of male speakers
        for spkr in speakers:
            if spkr in males_to_keep:
                sorted_speaker.remove((spkr,spk2dur[spkr]))
                sorted_speaker=[(spkr,spk2dur[spkr])]+sorted_speaker
            #if spkr in noisy:
            #    sorted_speaker.remove((spkr,spk2dur[spkr]))

 
        # Plot the Speech duration distribution, and superimpose a power law

        names=[spk_id for (spk_id,duration) in sorted_speaker]
        times=[duration for (spk_id,duration) in sorted_speaker]
        times_reduced=[format(u0/60,'.1f') for u0 in times]
        sns.set_context(rc={"figure.figsize":(8,4)})
        font={'weight' : 'bold', 
                'size' : 15}
        plt.rc('font',**font)

        total=self.corpus.duration(format='seconds')
        (spk_id0,duration0)=sorted_speaker[0]
        x_axis=range(0,len(names))
        barlist=plt.bar(x_axis,times,width=0.7,align="center",label="speech time",color=sns.xkcd_rgb["periwinkle"])
        
        ### Uncomment to plot with different colors for the genders
        # female/male proportions to 
        #x_male=[ind for (ind,spk_id) in enumerate(names) if spk_id in male]
        #x_female=[x for x in x_axis if x not in x_male]

        #male_bars=plt.bar(x_male,[times[i] for i in x_male],width=0.7,align="center"
                #,label="male speech time",color=sns.xkcd_rgb['light mauve'])
        #aa=[times[j] for j in x_female]
        #female_bars=plt.bar(x_female,[times[i] for i in x_female],width=0.7,
                #align="center",label="female speech time",color=sns.xkcd_rgb['periwinkle'])
            

        # Compute the distribution used to cut the corpus
        if function == "exponential":
            distrib=[duration0*exp(-0.4*(ind-1)) for ind in x_axis]
        elif function =="power-law":
            exponent=1
            distrib=[duration0/((ind)**exponent)+30 for ind in x_axis]
        elif function =="step":
            #number of speaker for which we keep the whole speech
            spk_threshold=new_speakers
            
            #duration of speech we keep for the other speakers : 
            dur_threshold=10*60
            distrib=times[0:spk_threshold]
            distrib[spk_threshold+1:len(times)]=[dur_threshold] *(len(times)-spk_threshold)
            distrib=[dist if dist<=dur else dur for dist,dur in zip(distrib,times)]
            
            #keep the speakers in the "family", to construct the test part
            family_temp=sorted_speaker[0:spk_threshold]
            family=[speaker for speaker,duration in family_temp]
            distrib=[dist if names[ind] not in noisy else 0 for (ind,dist) in enumerate(distrib)]
        elif function == "nothing":
            distrib=times
        
        

        self.limits=dict(zip(names,distrib))
                
        
        # Show Plot
        if plot==True:

            for j,txt in enumerate(times_reduced):
                if j!=0:
                    plt.annotate(txt,(x_axis[j]-1,times[j]+3),rotation=45)
            self.log.info('Speech duration for corpus : %i minutes',sum(times)/60)
            distrib_reduced=[format(u0/60,'.1f') for u0 in distrib]
            plt.scatter(x_axis,distrib,marker='o',color=sns.xkcd_rgb["cerise"],
                        label="Speech distribution (in minutes)")
            plt.plot(x_axis,distrib,color=sns.xkcd_rgb["cerise"])
            for i,txt in enumerate(distrib_reduced):
                plt.annotate(txt,(x_axis[i]-1,distrib[i]+2),rotation=45,)
            self.log.info('for %i speakers, the filter gives %i minutes of speech',
                    len(sorted_speaker),sum(distrib)/60)

            plt.legend() 
            plt.xticks(x_axis,names,rotation=45)
            plt.xlabel('speaker')
            plt.ylabel('duration (in minutes)',rotation=90)
        
            plt.show()
        

        ## write the names of the "family" speakers, to use them in the test
        if not THCHS30:
            return(self.filter_corpus(names,function))
        else:
            return(self.filter_THCHS30(names,function))

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
            if limits[speaker]==0:
                continue 

            for utts in spk2utts[speaker]:
                time+=utt2dur[utts]
                if utts=='M01_B23_C1_N_te_fr_3' or utts == 'M01_B23_C1_N_te_fr_4' or utts == 'M01_B23_C1_N_te_fr_5' or utts == 'M01_B23_C1_N_te_fr_2':
                    continue
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

    def filter_THCHS30(self,names,function):
        """split the THCHS30 corpus without having the same text for some speakers

        
        Return the subcorpus 
        """
        limit=self.limit
        time=0
        utt_ids=[]
        spk2utts=self.spk2utts
        utt2dur=self.utt2dur
        not_kept_utts=defaultdict(list)
        corpus=self.corpus
        
        
        # create list of utterances we want to keep, utterances we don't want to keep
        for speaker in self.THCHS30_family :
            all_utts = spk2utts[speaker]
            kept_utts = [utt for utt in all_utts if float(utt.split('_')[1])>limit[speaker[0]]]
            utt_ids = utt_ids+kept_utts

        for speaker in self.THCHS30_outsiders1:
            all_utts = spk2utts[speaker]
            limit_out1=limit[speaker[0]]-50
            kept_utts = [utt for utt in all_utts if float(utt.split('_')[1])<=limit_out1]
            utt_ids = utt_ids+kept_utts

        for speaker in self.THCHS30_outsiders2:
            all_utts = spk2utts[speaker]
            limit_out1=limit[speaker[0]]-50
            limit_out2=limit[speaker[0]]
            kept_utts = [utt for utt in all_utts if limit_out1<float(utt.split('_')[1])<=limit_out2]
            utt_ids = utt_ids+kept_utts
           

             
        # here we build the list of utts we remove, and we adjust the boundaries of
        # the other utterancess, in order to have correct timestamps
        for speaker in names: 
            offset=0
            for utt in spk2utts[speaker]:
                #for each wav, we compute the cumsum of the lengths of the utts we remove
                # in order to have correct timestamps for the other utts in the files
               
                wav_id,utt_tbegin,utt_tend=corpus.segments[utt]
                corpus.segments[utt]=(wav_id,utt_tbegin-offset,utt_tend-offset)

                if utt_tbegin-offset<0 or utt_tend-offset<0:
                    self.log.info('WARN : offset is greater than utterance boundaries')
                if utt not in utt_ids:
                    offset=offset+utt2dur[utt]
                    not_kept_utts[speaker].append((utt,corpus.segments[utt]))

        return(self.corpus.subcorpus(utt_ids,prune=True,name=function,validate=True),
                not_kept_utts);

    def librispeech_gender(self,path):
        """ construct the dict(speaker_id,gender) for librispeech """
        path=os.path.abspath(path)
        try:
            speaker_dict=open_utf8(path,'r')
        except IOError:
            self.log.info("Error: File not found at {}".format(path))
            return False
        for line in speaker_dict:
            if line[0]==";":
                continue
            spk_id,sex,subset,dur,name = line.split(" | ")
            subset.strip()
            sex.strip()
            spk_id.strip()

            #if subset is not "train-clean-360 ":
            #    print subset
            #    continue
            if len(spk_id)==2:
                spk_id='00'+spk_id
            elif len(spk_id)==3:
                spk_id='0'+spk_id
            self.gender[spk_id]=sex
            
    def write_family_set(self,family,out):
        out=os.path.join(os.path.dirname(out),'family')
        if not os.path.isdir(out):
            os.makedirs(out)
        out_path=os.path.join(out,'family.txt')

        with open(out_path,'w') as outf:
            for spkr in family:
                outf.write(u'{}\n'.format(spkr))


