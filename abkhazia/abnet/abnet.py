"""
@author Roland Thiolliere
"""

"""
This script contains functions to train an ABnet for a list of pairs of same words
and to calculate the embeddings using a trained ABnet.
"""

import os.path as p
import os

def train(same_pair_file, output_path,

          n_layers=2, same_different_word_ratio=0.5,
          same_different_speaker=None, feature_type='fbanks'):
    """
    Function to train an ABnet on a list of words

    It takes as input a list of pairs of same words. This file contains several lines in the format:
    wav1 start1 stop1 wav2 start2 stop2 spk-id1 spk-id2
    - wav1 and wav2 are wavefiles specified with their full path
    - start1, start2, stop1, stop2 are times in seconds
    - spk-id1 and spk-id2 are strings identifying uniquely the speakers

    Parameters:
        same_pair_file: string
            path to the input file. This file contains a list of pairs of same words.
	output_path: string
        n_layers: int
            number of hidden layers of the neural network
        same_word_ratio: float
            ratio "number of same word pairs" / "total number of pairs" for each training batch
        same_speaker_ratio: float
            ratio "number of same speaker pairs" / "total number of pairs" for each training batch
        feature_type: string
    """
    raise NotImplementedError


def decode(model_path, wavefile_list, output_file):
    """
    Function to calculate the embeddings for a list of wavefiles using a trained ABnet
    in the h5features format

    Parameters:
        model_path: string, path to the abnet
        wavefile_list: string, path to the list of wavefiles (wavefiles are specified by their full path, one file per line)
        output_file: string, path to the outputfile, it will contains the embeddings in h5features format
    """
    raise NotImplementedError
    
