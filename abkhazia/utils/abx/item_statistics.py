# -*- coding: utf-8 -*-
# Copyright 2015, 2016 Thomas Schatz
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


def plot_statistics(item_file, stat_file, tonal=False):
    try:
        pp = PdfPages(stat_file)

        min_thresholds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        db, _ = database.load(item_file)

        # ad hoc fix, for latex compatibility
        s1 = set(db['phone'])
        db['phone'] = [phone.replace("_", "-") for phone in db['phone']]
        s2 = set(db['phone'])
        assert len(s1) == len(s2), "Latex compatibility mixup!"

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
        nb_context_found = len(set(zip(db['prev-phone'], db['next-phone'])))
        print('global_context_proportion %f' % (nb_context_found/np.float(nb_possible_context)))
        #TODO plot this in a text file or in the pdf using smthg like
        # http://stackoverflow.com/questions/4018860/text-box-with-line-wrapping-in-matplotlib

        """
        def context_coverage(db, min_tresholds, other_bys):
            nb_contexts = [[] for t in min_thresholds]
            for g, df in db.groupby(other_bys):
                gg = df.groupby(other_bys + ['prev-phone', 'next-phone'])
                contexts = [[] for t in min_thresholds]
                for context, df2 in gg:
                    for i, threshold in enumerate(min_thresholds):
                        if len(df2) >= threshold:
                            contexts[i].append(context)
                for i in range(len(min_thresholds)):
                    nb_contexts[i].append(len(set(contexts[i])))
            for i in range(len(min_thresholds)):
                nb_contexts[i] = np.array(nb_contexts[i])
            return nb_contexts
        """

        def nb_x_per_y(db, min_tresholds, x, y, remaining=[]):
            # remaining should correspond to columns used to threshold
            # that are neither in x nor in y
            nb = [[] for t in min_thresholds]
            for _, dfy in db.groupby(y):
                nx = np.zeros(shape=(len(min_thresholds),), dtype=np.int)
                for _, dfx in dfy.groupby(x):
                    if remaining:
                        l = np.array([len(dfr) for _, dfr in dfx.groupby(remaining)])
                        p = [int(any(l >= threshold)) for threshold in min_thresholds]
                    else:
                        p = [int(len(dfx) >= threshold) for threshold in min_thresholds]
                    nx = nx + p
                for i in range(len(min_thresholds)):
                    nb[i].append(nx[i])
            for i in range(len(min_thresholds)):
                nb[i] = np.array(nb[i])
            return nb

        """
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
        """

        def plot_x_per_y(title, db, min_thresholds, x, y, remaining=[]):
            data = nb_x_per_y(db, min_thresholds, x, y, remaining)
            plt.figure()
            plt.boxplot(data, labels=min_thresholds)
            plt.title(title)
            plt.xlabel('Min threshold')
            pp.savefig()

        plot_x_per_y('Contexts found for each (speaker, phone) among the {0} possible contexts'.format(nb_possible_context),
                    db, min_thresholds,
                    ['prev-phone', 'next-phone'], ['talker', 'phone'])

        plot_x_per_y('Contexts found for each phone among the {0} possible contexts'.format(nb_possible_context),
                    db, min_thresholds,
                    ['prev-phone', 'next-phone'], ['phone'], ['talker'])

        plot_x_per_y('Contexts found for each speaker among the {0} possible contexts'.format(nb_possible_context),
                    db, min_thresholds,
                    ['prev-phone', 'next-phone'], ['talker'], ['phone'])

        plot_x_per_y('Speakers found for each phone',
                    db, min_thresholds,
                    ['talker'], ['phone'], ['prev-phone', 'next-phone'])

        plot_x_per_y('Speakers found for each phone + context',
                    db, min_thresholds,
                    ['talker'], ['phone', 'prev-phone', 'next-phone'])

        if tonal:
            plot_x_per_y('Tones found for each segment + context',
                    db, min_thresholds,
                    ['tone'], ['segment', 'prev-phone', 'next-phone'], ['talker'])

            plot_x_per_y('Tones found for each segment + context + speaker',
                    db, min_thresholds,
                    ['tone'], ['segment', 'prev-phone', 'next-phone', 'talker'])

            plot_x_per_y('Segments found for each tone + context',
                    db, min_thresholds,
                    ['segment'], ['tone', 'prev-phone', 'next-phone'], ['talker'])

            plot_x_per_y('Segments found for each tone + context + speaker',
                    db, min_thresholds,
                    ['segment'], ['tone', 'prev-phone', 'next-phone', 'talker'])

        """ TODO duration of sound/number of phone tokens by speaker, by phone or both """

    finally:
        pp.close()


root = '/Users/thomas/Documents/PhD/Recherche/test/'

item_file = root + 'BUC_phone.item'
stat_file = root + 'BUC_phone.pdf'
plot_statistics(item_file, stat_file, tonal=False)

"""
item_file = root + 'WSJ_phone.item'
stat_file = root + 'WSJ_phone.pdf'
plot_statistics(item_file, stat_file, tonal=False)
"""
