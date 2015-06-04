# -*- coding: utf-8 -*-
"""
Data preparation for buckeye

@author: Roland Thiolliere
"""

import os
import subprocess as sp
import codecs
import re
import importlib
import logging
import glob
import os.path as path
import tempfile
import shutil
from operator import itemgetter
from itertools import groupby

input_dir = '/home/xcao/cao/corpus_US/BUCKEYE/Buckeye_final_check'
class Buckeye(object):
    #root = '/fhgfs/bootphon/scratch/roland/abkhazia/corpora/buckeye'
    root = '/home/xcao/github_abkhazia/abkhazia/corpora/corpora/Buckeye'

    paths = {
        'wavs': path.join(root, 'data/wavs'),
        'utt_list': path.join(root, 'data/segments'),
        'spk_list': path.join(root, 'data/utt2spk'),
        'phones': path.join(root, 'data/phones.txt'),
        'text': path.join(root, 'data/text'),
        'silences': path.join(root, 'data/silences.txt'),
        'dict': path.join(root, 'data/lexicon.txt')
        }


    def Buckeye(self, input_dir, paths, verbose=1):
        self.wav_files = extract_wav(input_dir, paths['wavs'])
        self.wrd_files = list_wrds(input_dir)
        self.utts = {path.basename(wrd_file): extract_utt(wrd_file)
                     for wrd_file in self.wrd_files}
        self.extended_utts = utt_list(self.utts, self.wav_files, paths['utt_list'])
        spk_list(self.extended_utts, paths['spk_list'])
        extract_transcript(self.extended_utts, paths['text'])


def list_wavs(corpus_dir):
    return glob.glob(path.join(corpus_dir, '**/*/*.wav'))


def list_wrds(corpus_dir):
    return glob.glob(path.join(corpus_dir, '**/*/*.wrd'))


def extract_wav(input_dir, output_dir):
    """
    Copy the audio file in the wavs folder, and return the list of audio files
    """
    fs = 16000  # sampling frequency of the input files in Hz
    nbits = 16  # each sample is coded on 16 bit in the input files
    
    if not(os.path.isdir(output_dir)):
        os.mkdir(output_dir)
    l = list_wavs(input_dir)
    res = []
    for wavfile in l:
        bname = path.basename(wavfile)
        outfile = os.path.join(output_dir, bname)
        res.append(outfile)
        #shutil.copy(wavfile, outfile)
    return res


def extract_utt(wrd_file):
    """Extract utterances in a .wrd file, splitting on interviewer or third person talking
    Format should be the new .wrd format, without header

    Returns a list of fragments: (start, end, ([word, ..], [phone, ..]))
    """
    words = []
    threshold = 0.5
    with open(wrd_file) as fin:
        for line in fin:
            aux = line.strip().split('\t')
            trans = aux[2].split('; ')
            words.append((float(aux[0]), float(aux[1]), trans[0], trans[2]))
    
    # finding split indexes:
    # IVER, long sil/noise
    #TODO: merge silences/noise before applying threshold
    trans = [word[2] for word in words]
    split = ([0]
             + [i for i, w in enumerate(words)
                if w[2][:5] == '<IVER' or (w[2][0] == '<' and w[1] - w[0] > threshold)]
             + [len(words)-1])

    # extend split to surrounding silence/noise
    for prev_index, index, next_index in zip(split[:-2], split[1:-1], split[2:]):
        i = index - 1
        while i > prev_index and words[i][2][0] == '<':
            split.append(i)
            i -= 1
        i = index + 1
        while i < next_index and words[i][2][0] == '<':
            split.append(i)
            i += 1

    
    # split and flatten 'words' by 'split'
    diff = lambda l1,l2: [x for x in l1 if x not in l2]
    keep = diff(range(len(words)), split)
    ranges = []
    frags = []
    for k, g in groupby(enumerate(keep), lambda (i,x):i-x):
        group = map(itemgetter(1), g)
        frags.append((words[group[0]][0], words[group[-1]][1],
                     [words[index][2] for index in group],
                     [words[index][3] for index in group]))

    return frags


def utt_list(utterances, wav_files, output_file):
    """Write the utterance list from the wav files list and the utterances list
    Return the new utterances ids expanded (one utterance per fragment)
    """
    new_utts = []
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for f in wav_files:
            utt_id = path.basename(f)[:-4]
            for i, utt_data in enumerate(utterances[utt_id]):
                new_utt = utt_id + '_{}'.format(i)
                new_utts[new_utt] = utt_data
                out.write(u"{0} {1} {2} {3}\n"
                          .format(new_utt, f, utt_data[0], utt_data[1]))
    return new_utts


def spk_list(utt_list, output_file):
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for utt_id in utt_list:
            spk_id = f[:3]
            out.write(u"{0} {1}\n".format(utt_id, spk_id))


def extract_transcript(utterances, output_file):
    """Write the text transcription for each utterances (expanded utterances)
    """
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for utt_id, utt_data in utterances.iteritems():
            out.write(u'{} {}\n'.format(utt_id, ' '.join(utt_data[2][0])))

"""
def export_phones(utterances, output_file, silences=None, silence_file=None):

    Extract the list of phones in the corpus

    phone_inventory = set()
    for utt_data in utterances.itervalues():
        for phone = utt_data[2][1]:
            phone_inventory.add(phone)
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        out.write('\n'.join(phone_inventory))
    
    if silences is not None:
        with codecs.open(silence_file, mode='w', encoding='UTF-8') as out:
            for sil in silences:
                out.write(sil + u"\n")
"""