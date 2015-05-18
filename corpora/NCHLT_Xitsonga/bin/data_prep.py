# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
Data preparation for Xitsonga
"""

import os
import re
import shutil



# paths - needs to change paths and versions of Xitsonga
# create 'data' directory if doesn't exist
# phones.txt should be distributed?
# in silences.txt: added NSN - can do that once have run validate_corpus.txt

raw_path = "/fhgfs/bootphon/data/raw_data/NCHLT/nchlt_Xitsonga/"
#derived_path = "/fhgfs/bootphon/data/derived_data/NCHLT_abkhazia/Xitsonga/"
derived_path = "/home/xcao/derived_data_oberon//NCHLT_abkhazia/Xitsonga/"
dict_path = "/fhgfs/bootphon/data/raw_data/CMU_dict/"
#abkhazia_path_data = "/fhgfs/bootphon/scratch/xcao/github_abkhazia/abkhazia/corpora/NCHLT_Xitsonga/data/"
#abkhazia_path = "/fhgfs/bootphon/scratch/xcao/github_abkhazia/abkhazia/corpora/NCHLT_Xitsonga/"
abkhazia_path_data = "/home/xcao/github_abkhazia/abkhazia/corpora/NCHLT_Xitsonga/data/"
abkhazia_path = "/home/xcao/github_abkhazia/abkhazia/corpora/NCHLT_Xitsonga/"



#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################

#If generating the data for the first time, run all steps
#Otherwise, start from step 3 to just link the wavs rep. (wavs already available in /fhgfs/bootphon/data/derived_data/Xitsonga_abkhazia/NCHLT_abkhazia/Xitsonga/)

#STEP 1
# filter out .DS_Store files from MacOS if any
def list_dir(d):
	return [e for e in os.listdir(d) if e != '.DS_Store']


#STEP 2
#copy all wavs files into one wavs directory in "derived data"
#Arguments are name of destination folder ("wavs")
def copy_wav(o):
    #create wirs dir
    output_dir = os.path.join(derived_path, o)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    #walk recursively and copy all the wav files to one folder
    input_dir_wav = os.path.join(raw_path, "audio")
    for dirpath, dirs, files in os.walk(input_dir_wav):
        for f in files:
            #checkfor wav files and copy them
            m_file = re.match("(.*)\.wav", f)
            if m_file:
                filename = os.path.join(dirpath,f)
                dest_filename = os.path.join(output_dir,f)
                shutil.copy2(filename, dest_filename)
                print ('finished copying ' + filename)
    #rename all wav files so that wav files start by speaker_ID
    for dirpath, dirs, files in os.walk(output_dir):
        for f in files:
            filename = os.path.join(dirpath,f)
            os.rename(filename, filename.replace("nchlt_tso_", ""))

#STEP 3
#link speech folder to the data kaldi directory
def link_wavs():
    wavs_path = os.path.join(abkhazia_path_data, "wavs")
    wavs_path_src = os.path.join(derived_path, 'wavs')
    logs_path = os.path.join(abkhazia_path, "logs")
    #if wavs folder doesn't exist, create symbolic link to speech data
    if not os.path.isdir(wavs_path):
        os.symlink(wavs_path_src, wavs_path)
    #if already exists, remove folder and all files and re-create symbolic link to speech data
    else:
        #unlink folder
        os.unlink(wavs_path)
        #remove folder
        shutil.rmtree(wavs_path, ignore_errors=True)
        #create symlink
        os.symlink(wavs_path_src, wavs_path)
    #if logs folder doesn't exist, create folder
    if not os.path.isdir(logs_path):
        os.makedirs(logs_path)
    print ('finished linking wavs directory and creating logs directory')


#STEP 5
#Create segments file: <utterance-id> <wav-filename>
#Create speakers file: <utterance-id> <speaker-id>
def segments_speakers():
    utt_list = []
    output_file_segment = open(os.path.join(abkhazia_path_data, 'segments.txt'), 'w')
    output_file_speaker = open(os.path.join(abkhazia_path_data, 'utt2spk.txt'), 'w')
    input_dir_wav = os.path.join(derived_path, "wavs")
    #list all files in wav folder
    files = os.listdir(input_dir_wav)
    #get basename from file to get utt_ID
    for filename in files:
        utt_ID = os.path.splitext(filename)[0]
        #create a list with all utt_ID
        utt_list.append(utt_ID)
        #write segments file
        output_file_segment.write(utt_ID + ' ' + filename + '\n')
        #extract the first 3 characters from filename to get speaker_ID
        m_speaker = re.match("(.*)_(.*).wav", filename)
        if m_speaker:
            speaker_ID = m_speaker.group(1)
            #write utt2spk file
            output_file_speaker.write(utt_ID + ' ' + speaker_ID + '\n')
    print ('finished creating segments and speakers files')

def text():
    list_utt = []
    list_info = []
    list_total = []
    infile_segment = open(os.path.join(abkhazia_path_data, 'segments.txt'), 'r')
    #get all the utt ID to make sure that the trs match with teh wav files
    for line in infile_segment:
        m_segment = re.match('(.*) (.*)', line)
        if m_segment:
            utt =  m_segment.group(1)
            list_utt.append(utt)
    infile_segment.close()
    
    output_file_text = open(os.path.join(abkhazia_path_data, 'text.txt'), 'w')
    input_dir_trs = os.path.join(raw_path, "transcriptions")
    for dirpath, dirs, files in os.walk(input_dir_trs):
        for f in files:
            #get all the xml transcription files 
            m_xml = re.match("(.*).xml", f)
            if m_xml:
                with open(os.path.join(dirpath, f),) as infile:
                    #store each file as one string and split by tag
                    data = ' '.join([line.replace('\n', '') for line in infile.readlines()])
                    list_info = data.split('</recording>')
                infile.close()
                #append the list to the main list
                list_total.extend(list_info)
    print ("finished extracting the recording tags")
    #Go through each recording and extract the text and utt_ID according to pattern
    for i in list_total:
        m_text = re.match("(.*)<recording audio=(.*).wav(.*)<orth>(.*)</orth>", i)
        if m_text:
            utt_ID = m_text.group(2)
            text = m_text.group(4)
            #remove beginning of wav path to have utt_ID
            utt_ID = re.sub("(.*)nchlt_tso_", "", utt_ID)
            #replace [s] by <NOISE>
            text = text.replace("[s]", "<NOISE>")
            #check that the text has the equivalent wav and write to outfile
            if utt_ID in list_utt:
                output_file_text.write(utt_ID + ' ' + text + '\n')
            else:
                print(utt_ID)
    print ('finished creating text file')


#to do this, we need to get the mlfs for the language. Not sure it is available on the NCHLT website
def lexicon():
    list_total = []
    list_file = []
    list_line = []
    list_word = []
    list_phn = []
    dict_word = {}
    outfile_lexicon = open(os.path.join(abkhazia_path_data, 'lexicon.txt'), 'w')
    outfile_temp = open(os.path.join(abkhazia_path, 'logs/temp.txt'), 'w')
    input_dir_mlf = os.path.join(raw_path, "mlfs_tso")
    for dirpath, dirs, files in os.walk(input_dir_mlf):
        for f in files:
            #get all the nchlt mlf files 
            m_mlf = re.match("(.*)nchlt.mlf", f)
            if m_mlf:
                with open(os.path.join(dirpath, f), 'r') as infile:
                    #join all lines together into one string but still keeping new line character
                    data = '\n'.join([line.replace('\n', '') for line in infile.readlines()])
                    #split into a list of files ("." is the separator)
                    list_file = re.split('\.\n', data)
                #increment the total list which will be a list containing all small files
                list_total.extend(list_file)
                infile.close()

    #Go through each small file      
    for i in list_total:
        #split into a list of words (separator is "[0-9]+ [0-9]+ sp (.*)")
        list_word = re.split('[0-9]+ [0-9]+ sp (.*)', i)
        for w in list_word:
            w = w.strip()
            #split into lines
            list_line = w.split('\n')
            for l in list_line:
                #split each line into tokens
                list_phn = l.split()
                #if the line contains the word, extract word + phone
                if (len(list_phn) == 5):
                    #exclude the silence word
                    if (list_phn[4] == 'SIL-ENCE'):
                        continue
                    #otherwise, extract just phone corresponding to word already extracted
                    else:
                        outfile_temp.write(list_phn[4] + '\t' + list_phn[2])
                elif (len(list_phn) == 4):
                    outfile_temp.write(' ' + list_phn[2])
            outfile_temp.write('\n')
    outfile_temp.close()
    print ('finished writing temp file')
    
    #open temp dictionary
    infile_temp = open(os.path.join(abkhazia_path, 'logs/temp.txt'), 'r')
    #add these 2 entries in the dict
    outfile_lexicon.write ('<noise> NSN\n')
    outfile_lexicon.write ('<unk> SPN\n')
    for line in infile_temp:
        line = line.strip()
        m_file = re.match("(.*)\t(.*)", line)
        if m_file:
            word = m_file.group(1)
            phn = m_file.group(2)
            #if word not in the lexicon, add entry
            if word not in dict_word:
                if (word == "[s]"):
                    continue
                else:
                    dict_word[word] = phn
    #write lexicon to file, sorted by alphabetical order
    for w in sorted(dict_word):
            outfile_lexicon.write (w + ' ' + dict_word[w] + '\n')
    infile_temp.close()
    print ('finished creating lexicon file')
    #remove temp file
    os.remove(os.path.join(abkhazia_path, 'logs/temp.txt'))

def copy_phones():
    #copy phones file from bin to data folder
    filename = os.path.join(abkhazia_path, 'bin/phones.txt')
    dest_filename = os.path.join(abkhazia_path_data, 'phones.txt')
    shutil.copy2(filename, dest_filename)
    print ('finished copying phone file')

#Running the different steps
#copy_wav ('wavs')
link_wavs()
#segments_speakers()
#text()
#lexicon()
#copy_phones()
