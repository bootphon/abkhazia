# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 03:11:30 2014

@author: Thomas Schatz

Plot summary statistics about a standard .item file in a pdf file.

Should probably be merged at least partially with corpus_statistics.py...
"""

#TODO need to finish adaptation of this file to abkhazia
# this gives statistics about phones + talkers + phonetic context
# does nothing at the word level

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import ABXpy.database.database as database
# use latex for text rendering in figures
from matplotlib import rc
rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
rc('text', usetex=True)
# ipa font
matplotlib.rcParams['text.latex.preamble'] = ['\\usepackage{tipa}']

from matplotlib.backends.backend_pdf import PdfPages

def plot_statistics(item_file, stat_file):
    try:
        pp = PdfPages(stat_file)

        min_thresholds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        db, _ = database.load(item_file)
        
        """ tokens by type """
        distrib = np.array([len(df) for g, df in db.groupby(['phone', 'talker', 'prev-phone', 'next-phone'])])
        plt.figure()
        plt.hist(distrib, 100)
        plt.title('Histogram of the number of phone-talker-context types as a function of the number of tokens')
        plt.yscale('log', nonposy='clip')
        plt.xlabel('Number of tokens')
        plt.ylabel('Number of types')
        pp.savefig()
        
        thr = 20
        many_tokens = [(g, len(df)) for g, df in db.groupby(['phone', 'talker', 'prev-phone', 'next-phone']) if len(df) >= 150]
        many_tokens.sort(key=lambda e: e[1])  # sort according to length
        many_tokens = many_tokens[-thr:]
        print('{0} Types with the most tokens:\n'.format(thr))
        print(many_tokens)
        #TODO plot this in a text file or in the pdf using smthg like
        # http://stackoverflow.com/questions/4018860/text-box-with-line-wrapping-in-matplotlib
        
        p = []
        for threshold in min_thresholds:
            p.append(len(np.where(distrib >= threshold)[0])/np.float(len(distrib)))
        plt.figure()
        plt.plot(min_thresholds, p, '.-')
        plt.title('Proportion of types retained as a function of min threshold') 
        plt.xlabel('Min threshold')
        plt.ylabel('Proportion of types of items retained')
        pp.savefig()
        
        """ number of phonetic contexts by phone """
        nb_context = [(phone, len(df.groupby(['prev-phone', 'next-phone']).groups)) for phone, df in db.groupby(['phone'])]
        nb_context.sort(key=lambda e: e[1])
        phones, nb_context = zip(*nb_context)
        plt.figure()
        plt.plot(nb_context, 'o')
        plt.xlabel('Phones')
        plt.ylabel('Number of contexts')
        plt.xticks(np.arange(len(phones)), phones, fontsize=10)
        plt.title('Number of phonetic contexts for each phone')  
        #TODO bar plot + autosize x label font
        pp.savefig()
        
        """ contexts representation """
        nb_possible_context = len(phones)*len(phones)
        nb_context_found = len(set(db['prev-phone', 'next-phone']))
        print('global_context_proportion %f' % (nb_context_found/np.float(nb_possible_context)))
        #TODO plot this in a text file or in the pdf using smthg like
        # http://stackoverflow.com/questions/4018860/text-box-with-line-wrapping-in-matplotlib
        
        
        def context_coverage(db, min_tresholds, g1, g2=[]):
            nb_contexts = [[] for t in min_thresholds]
            for g, df in db.groupby(g1):
                gg = df.groupby(g2+['prev-phone', 'next-phone'])
                contexts = [[] for t in min_thresholds]
                for context, df2 in gg:
                    if g2:
                        context = context[-1]
                    for i, threshold in enumerate(min_thresholds):
                        if len(df2) >= threshold:
                            contexts[i].append(context)
                for i in range(len(min_thresholds)):
                    nb_contexts[i].append(len(set(contexts[i])))
            for i in range(len(min_thresholds)):               
                nb_contexts[i] = np.array(nb_contexts[i])
            return nb_contexts
            
        nb_contexts_by_phone_talker = context_coverage(db, min_thresholds, ['talker', 'phone'])
        #for i in range(len(min_thresholds)):
        #    nb_contexts_by_phone_talker[i] = nb_contexts_by_phone_talker[i]/np.float(nb_context_found)
        plt.figure()
        plt.boxplot(nb_contexts_by_phone_talker, labels=min_thresholds)
        plt.title('Contexts found for each (speaker, phone) among the 2209 possible contexts')
        plt.xlabel('Min threshold')
        pp.savefig()
        
        nb_contexts_by_phone = context_coverage(db, min_thresholds, 'phone', ['talker'])
        #for i in range(len(min_thresholds)):
        #    nb_contexts_by_phone[i] = nb_contexts_by_phone[i]/np.float(nb_context_found)
        plt.figure()
        plt.boxplot(nb_contexts_by_phone, labels=min_thresholds)
        plt.title('Contexts found for each phone among the 2209 possible contexts')
        plt.xlabel('Min threshold')
        pp.savefig()
        #TODO number of speakers for each phone as a function of threshold
        """
        n_talker_by_phone = {}
        for g, df in db.groupby('phone'):
            n_talker = [0 for i in range(len(min_thresholds))]
            for gg, df2 in df.groupby('talker'):
                lengths = [len(df3) for ggg, df3 in df2.groupby('context')]
                for i, threshold in enumerate(min_thresholds):
                    if any(lengths >= threshold):
                        n_talker[i] = n_talker[i]+1
            n_talker_by_phone[g] = n_talker
        for phone in n_talker_by_phone:
            plt.figure()
            plt.plot(min_thresholds, n_talker_by_phone[phone], '.-')
            plt.xlabel('Min threshold')
            plt.ylabel('Number of talker with phone %s' % phone)
            plt.title(phone)
        """    
            
        nb_contexts_by_talker = context_coverage(db, min_thresholds, 'talker', ['phone'])
        #for i in range(len(min_thresholds)):
        #    nb_contexts_by_talker[i] = nb_contexts_by_talker[i]/np.float(nb_context_found)
        plt.figure()
        plt.boxplot(nb_contexts_by_talker, labels=min_thresholds)
        plt.title('Contexts found for each speaker among the 2209 possible contexts')
        plt.xlabel('Min threshold')
        pp.savefig()
        
        """ TODO duration of sound/number of phone tokens by speaker, by phone or both """

    finally:
        pp.close()


root = '/Users/thomas/Documents/PhD/Recherche/test/'
item_file = root + 'CSJ_threshold_10.item'
stat_file = root + 'CSJ_threshold_10.pdf'
plot_statistics(item_file, stat_file)
