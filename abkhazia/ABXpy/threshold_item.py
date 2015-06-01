# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 17:07:55 2014

@author: Thomas Schatz
"""
import codecs
import pandas as pd
import numpy as np
import ABXpy.database.database as database

#TODO this file should be incorporated to ABXpy instead of abkhazia

# Note that randomness is probably reproducible on the same machine with the same python
# version, but I'm not sure what would happen on different machines or with different python
# versions

def threshold_item(item_file, output_file, columns, lower_threshold=1, upper_threshold=np.inf, seed=0):
    """
    Randomly sample items in item_file in order to limit the number of element in each cell
    to upper_threshold, where a cell is defined as a unique value of the specified columns 
    """
    np.random.seed(seed)
    # read input file
    with codecs.open(item_file, mode='r', encoding='UTF-8') as inp:
        header = inp.readline()
    db, _, feat_db = database.load(item_file, features_info=True)
    db = pd.concat([feat_db, db],axis=1)
    # group and sample
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        out.write(header)
        for group, df in db.groupby(columns):
            if len(df) >= lower_threshold:
                df = df.reindex(np.random.permutation(df.index))  # shuffle dataframe
                m = min(upper_threshold, len(df))
                df = df.iloc[:m]            
                for i in range(m):
                    out.write(u" ".join([unicode(e) for e in df.iloc[i]]) + u"\n")


root = '/Users/thomas/Documents/PhD/Recherche/test/'
corpus = 'CSJ_phone'  # 'WSJ_phone'
item_file = root + corpus + '.item'
lower_threshold= 2
upper_threshold = 3
out_file = root + corpus + '_threshold_' + str(lower_threshold) + '_' + str(upper_threshold) + '.item'
columns = ['phone', 'talker']  #['phone', 'prev-phone', 'next-phone', 'talker']                 
threshold_item(item_file, out_file, columns, lower_threshold=lower_threshold, upper_threshold=upper_threshold)
