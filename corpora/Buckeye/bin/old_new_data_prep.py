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


def list_wavs(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.wav", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list
    #return glob.glob(path.join(corpus_dir, '**/*/*.wav'))


def list_wrds(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.wrd", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
                  print (f)
    return file_list
    #return glob.glob(path.join(corpus_dir, '**/*/*.wrd'))
    
    
def list_utts(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.txt", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
                  #print (f)
    return file_list


def extract_wav(input_dir, output_dir):
    """
    Copy the audio file in the wavs folder, and return the list of audio files
    """
    l = list_wavs(input_dir)
    res = []
    for wavfile in l:
        bname = path.basename(wavfile)
        outfile = os.path.join(output_dir, bname)
        res.append(outfile)
        shutil.copy2(wavfile, outfile)
    return res


def extract_utt(input_dir, output_file):
    """Extract utterances in a .wrd file, splitting based on the utterances listed in the txt files

    Returns a list of fragments: <utterance-id> <wav-filename> <segment-begin> <segment-end>
    """
    outfile = open (output_file, "w")
    input_txt = list_utts(input_dir)
    length_utt = {}
    for utts in input_txt:
        with open (utts) as infile_txt:
            print(utts)
            current_index = 0
            j = 0
            lines = infile_txt.readlines()
            bname = os.path.basename(utts)
            bname_word = bname.replace('txt', 'wrd')
            bname_wav = bname.replace('txt', 'wav')
            utt = bname.replace('.txt', '')
            for line in lines:
                line.strip('\n')
                #print (line)
                words = line.split(' ')
                length_utt[j] = len(words)
                j = j+1
            """
            for n in length_utt:
                outfile.write (utts + str(n) + '\t' + str(length_utt[n]) + '\n')
            """
            wrd = os.path.join(wrd_dir, bname_word)
            with open (wrd) as infile_wrd:
                lines_2 = []
                lines_2 = infile_wrd.readlines()
                #print("counter for wrd file:" + str(len(lines_2)) + '\n')
                """
                match_intro = re.match('.*{B_TRANS}; B; B; null', line)
                if match_intro:
                    del lines_2[line]
                """
                for n in length_utt:
                    print len(lines_2)
                    print current_index
                    if (n == 0):
                        onset_line = str(lines_2[n])
                        match_onset = re.match('(.*)\t(.*)\t(.*)', onset_line)
                        if not match_onset:
                            raise IOError
                        onset = match_onset.group(1)
                        outfile.write(utt + '-sent' + str(n+1) + ' ' + bname_wav + ' ' + str(onset) + ' ')
                        index_offset = length_utt[n]
                        offset_line = lines_2[index_offset-1]
                        match_offset = re.match('(.*)\t(.*)\t(.*)', offset_line)
                        if match_offset:
                            offset = match_offset.group(1)
                            outfile.write(str(offset))
                            current_index = index_offset
                            outfile.write('\n')
                            #outfile.write(str(current_index) + '\n')
                        #outfile.write(offset_line + '\n')
                    else:
                        onset_line = str(lines_2[current_index])
                        match_onset = re.match('(.*)\t(.*)\t(.*)', onset_line)
                        if match_onset:
                            onset = match_onset.group(1)
                            outfile.write(utt + '-sent' + str(n+1) + ' ' + bname_wav + ' ' + str(onset) + ' ')
                        index_offset = length_utt[n]+current_index
                        #outfile.write("index offset line: " + str(index_offset))
                        offset_line = lines_2[index_offset-1]
                        match_offset = re.match('(.*)\t(.*)\t(.*)', offset_line)
                        if match_offset:
                            offset = match_offset.group(2)
                            outfile.write(str(offset))
                            current_index = index_offset
                            outfile.write('\n')
                            #outfile.write(str(current_index) + '\n')
                        #outfile.write(offset_line + '\n')
                        #print(onset_line)



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
#######################################################################################
#######################################################################################
##################################### Parameters ######################################
#######################################################################################
#######################################################################################

# Raw distribution of LibriSpeech is available at: http://www.openslr.org/12/
raw_buckeye_path = "/home/xcao/cao/corpus_US/BUCKEYE/Buckeye_final_check"

# path to CMU dictionary as available from http://www.speech.cs.cmu.edu/cgi-bin/cmudict (free)
# the recipe was designed using version 0.7a of the dictionary, but other recent versions
# could probably be used without changing anything
# complementing with the LibriSpeech dict which contains the words not found in the cmu (not exhaustive list however)
# available for download at http://www.openslr.org/11/
raw_cmu_path = "/fhgfs/bootphon/data/raw_data/CMU_dict/"
dict_buckeye_path = "/fhgfs/bootphon/data/raw_data/LibriSpeech/"

# flac is required for converting .flac to .wav.
flac = "/usr/bin/flac"

# Path to a directory where the processed corpora is to be stored
output_dir = "/home/xcao/github_abkhazia/abkhazia/corpora/Buckeye/"

#######################################################################################
#######################################################################################
###################################### Main part ######################################
#######################################################################################
#######################################################################################


# setting up some paths and directories
data_dir = os.path.join(output_dir, 'data')
if not os.path.isdir(data_dir):
    os.makedirs(data_dir)
wav_dir = os.path.join(data_dir, 'wavs')
if not os.path.isdir(wav_dir):
    os.makedirs(wav_dir)


"""
STEP 1 - Setting up wav folder
This step can take a lot of time
"""
#list_wavs(raw_buckeye_path)
#extract_wav(raw_buckeye_path, wav_dir)
#print("Copied wavefiles")


output_file = os.path.join(data_dir, 'segments.txt')
utt_dir = os.path.join(raw_buckeye_path, 'orig_txt_adjusted')
wrd_dir = os.path.join(raw_buckeye_path, 'wrd')
extract_utt(utt_dir, output_file)