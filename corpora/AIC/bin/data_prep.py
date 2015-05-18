# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
Data preparation AIC - LSCP version
"""

import os
import re
import shutil



# paths - needs to change paths and versions of Librispeech
# create 'data' directory if doesn't exist
raw_path = "/home/xcao/cao/projects/LDC_distribution/data/"
cmu_path = "/home/xcao/cao/corpus_US/CMU_dict/"
abkhazia_path_data = "/home/xcao/github_abkhazia/abkhazia/corpora/AIC/data/"
abkhazia_path = "/home/xcao/github_abkhazia/abkhazia/corpora/AIC/"

#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################

#STEP 1
# filter out .DS_Store files from MacOS if any
def list_dir(d):
	return [e for e in os.listdir(d) if e != '.DS_Store']


#STEP 2
#link speech folder to the data kaldi directory
def link_wavs():
    wavs_path = os.path.join(abkhazia_path_data, "wavs")
    wavs_path_src = os.path.join(raw_path, 'speech')
    logs_path = os.path.join(abkhazia_path, "logs")
    #if wavs folder doesn't exist, create symbolic link to speech data
    if not os.path.isdir(wavs_path):
        os.symlink(wavs_path_src, wavs_path)
    #if already exists, remove folder and re-create symbolic link to speech data
    else:
        os.remove(wavs_path)
        os.symlink(wavs_path_src, wavs_path)
    #if logs folder doesn't exist, create folder
    if not os.path.isdir(logs_path):
        os.makedirs(logs_path)
    print ('finished linking wavs directory and creating logs directory')
     

#STEP 3
#Create segments file: <utterance-id> <wav-filename>
#Create speakers file: <utterance-id> <speaker-id>
#Argument is name of wav directory
def segments_speakers():
    output_file_segment = os.path.join(abkhazia_path_data, 'segments.txt')
    output_file_speaker = os.path.join(abkhazia_path_data, 'utt2spk.txt')
    outfile1 = open(output_file_segment, "w")
    outfile2 = open(output_file_speaker, "w")
    #get filenames from wavs folder
    wav_input_dir = os.path.join(abkhazia_path_data, 'wavs')
    files = os.listdir(wav_input_dir)
    for filename in files:
        #split filename by "-" and get the first elt as speaker_ID
        filename_split = filename.split("_")
        speaker_ID = filename_split[0]
        #get basename of the file as utt_ID
        utt_ID = os.path.splitext(filename)[0]
        outfile1.write(utt_ID + ' ' + filename + '\n')
        outfile2.write(utt_ID + ' ' + speaker_ID + '\n')
    print ('finished creating segments and speakers files')
    outfile1.close()
    outfile2.close()


#STEP 4
#Create text file: <utterance-id> <word1> <word2> ... <wordn>
def text():
    #normal_weird_combined.txt a merge of weird.txt and normal.txt
    #it corresponds to text.txt so should just create a symbolic link
    #if not distributed, merge between the 2.Otherwise just append the 2
    original_text_path = os.path.join(raw_path, "text/normal_weird_combined.txt")
    dest_text_path = os.path.join(abkhazia_path_data,"text.txt")
    #if file exists, just create symbolic link
    if os.path.isdir(original_text_path):
        os.symlink(original_text_path, dest_text_path)
    #else, merge the 2 files
    else:
        input_file = os.path.join(raw_path, 'text/normal.txt')
        input_file2 = os.path.join(raw_path, 'text/weird.txt')
        infile = open(input_file, "r")
        infile2 = open(input_file2, "r")
        outfile = open(dest_text_path, "w")
        for line in infile:
            outfile.write(line)
        for line in infile2:
            outfile.write(line)
    print ('finished creating text file')
    infile.close()
    infile2.close()
    outfile.close()


#STEP 5
#Create temp lexicon file and temp OOVs
#No transcription for the words, we will use the CMU but will need to convert to the symbols used in the AIC
def temp_cmu_lexicon():
    dict_word = {}
    cmu_dict = {}
    infile = open(os.path.join(cmu_path, 'cmudict.0.7a'), 'r')
    #open CMU dict
    for line in infile:
        dictionary = re.match("(.*)\s\s(.*)", line)
        if dictionary:
            entry = dictionary.group(1)
            phn = dictionary.group(2)
            #remove pronunciation variants
            phn = phn.replace("0", "")
            phn = phn.replace("1", "")
            phn = phn.replace("2", "")
            #create the combined dictionary
            cmu_dict[entry] = phn;
    infile.close()
    infile2 = open(os.path.join(abkhazia_path_data, 'text.txt'), 'r')
    output_file_text = os.path.join(abkhazia_path, 'logs/temp_lexicon_cmu.txt')
    output_file_text2 = os.path.join(abkhazia_path, 'logs/temp_OOV.txt')
    outfile = open(output_file_text, "w")
    outfile2 = open(output_file_text2, "w")
    for line in infile2:
        m = re.match("([fm0-9]+)_([ps])_(.*?)\s(.*)", line)
        if m:
            utt = m.group(4)
            words = utt.split()
            for word in words:
                word = word.upper()
                if word not in dict_word:
                    dict_word[word] = 1
                else:
                    dict_word[word] += 1
    infile2.close()
    #Loop through the words in prompts by descending frequency and create the lexicon by looking up in the CMU dictionary
    #OOVs should be the sounds and will be written in temp OOV.txt
    for w, f in sorted(dict_word.items(), key=lambda kv: kv[1], reverse=True):
        if w in cmu_dict.viewkeys():
            outfile.write (w + ' ' + cmu_dict[w] + '\n')
        else:
            outfile2.write(w + '\t' + str(f) + '\n')
    print ('finished creating lexicon file')


#STEP 6
#Create lexicon file: <word> <phone_1> <phone_2> ... <phone_n>
def lexicon():
    array_phn = []
    output_file_text = os.path.join(abkhazia_path_data, 'lexicon.txt')
    outfile = open(output_file_text, "w")
    output_file_text2 = os.path.join(abkhazia_path, 'logs/OOV.txt')
    outfile2 = open(output_file_text2, "w")
    infile = open(os.path.join(abkhazia_path, 'logs/temp_lexicon_cmu.txt'), 'r')
    infile2 = open(os.path.join(abkhazia_path, 'logs/temp_OOV.txt'), 'r')
    for line in infile:
        #non greedy match to extract phonetic transcription
        m = re.match("(.*?)\s(.*)", line)
        if m:
            word = m.group(1)
            word = word.lower()
            phn_trs = m.group(2)
            #Convert the CMU symbols to AIC symbols
            phn_trs = phn_trs.replace('AA' , 'a')
            phn_trs = phn_trs.replace('AE' , 'xq')
            phn_trs = phn_trs.replace('AH' , 'xa')
            phn_trs = phn_trs.replace('AO' , 'c')
            phn_trs = phn_trs.replace('AW' , 'xw')
            phn_trs = phn_trs.replace('AY' , 'xy')
            phn_trs = phn_trs.replace('DH' , 'xd')
            phn_trs = phn_trs.replace('EH' , 'xe')
            phn_trs = phn_trs.replace('ER' , 'xr')
            phn_trs = phn_trs.replace('EY' , 'e')
            phn_trs = phn_trs.replace('CH' , 'xc')
            phn_trs = phn_trs.replace('HH' , 'h')
            phn_trs = phn_trs.replace('IH' , 'xi')
            phn_trs = phn_trs.replace('IY' , 'i')
            phn_trs = phn_trs.replace('JH' , 'xj')
            phn_trs = phn_trs.replace('NG' , 'xg')
            phn_trs = phn_trs.replace('OW' , 'o')
            phn_trs = phn_trs.replace('OY' , 'xo')
            phn_trs = phn_trs.replace('SH' , 'xs')
            phn_trs = phn_trs.replace('TH' , 'xt')
            phn_trs = phn_trs.replace('UH' , 'xu')
            phn_trs = phn_trs.replace('UW' , 'u')
            phn_trs = phn_trs.replace('ZH' , 'xz')
            phn_trs = phn_trs.replace('D' , 'd')
            phn_trs = phn_trs.replace('B' , 'b')
            phn_trs = phn_trs.replace('F' , 'f')
            phn_trs = phn_trs.replace('G' , 'g')
            phn_trs = phn_trs.replace('K' , 'k')
            phn_trs = phn_trs.replace('L' , 'l')
            phn_trs = phn_trs.replace('M' , 'm')
            phn_trs = phn_trs.replace('N' , 'n')
            phn_trs = phn_trs.replace('P' , 'p')
            phn_trs = phn_trs.replace('R' , 'r')
            phn_trs = phn_trs.replace('S' , 's')
            phn_trs = phn_trs.replace('T' , 't')
            phn_trs = phn_trs.replace('V' , 'v')
            phn_trs = phn_trs.replace('W' , 'w')
            phn_trs = phn_trs.replace('Y' , 'y')
            phn_trs = phn_trs.replace('Z' , 'z')
            outfile.write(word + ' ' + phn_trs + '\n')
    #for the sounds
    for line in infile2:
        m = re.match("(.*)\t(.*)", line)
        if m:
            sound = m.group(1)
            sound = sound.lower()
            freq = m.group(2)
            freq = int(freq)
            #discard the OOV with freq 1 because they are the typos. They will remain OOVs
            if (freq > 1):
                phn_trs = sound
                #need to split the sound into phones to have the phonetic transcription
                array_phn = phn_trs.split(":")
                outfile.write(sound)
                for p in array_phn:
                    outfile.write(' ' + p)
                outfile.write('\n')
            else:
                outfile2.write(sound + '\n')
    #remove the temp files
    os.remove('/home/xcao/github_abkhazia/abkhazia/corpora/AIC/logs/temp_lexicon_cmu.txt')
    os.remove('/home/xcao/github_abkhazia/abkhazia/corpora/AIC/logs/temp_OOV.txt')


#STEP 7
#Copy phone files - should be distributed in the new AIC version
def copy_phones():
    phone_src = os.path.join(raw_path, 'phones.txt')
    phone_dest = os.path.join(abkhazia_path_data, 'phones.txt')
    if not os.path.isdir(phone_dest):
        shutil.copy2(phone_src, phone_dest)


#Running the different steps
#link_wavs()
#segments_speakers()
#text()
#temp_cmu_lexicon()
#lexicon()
copy_phones()




