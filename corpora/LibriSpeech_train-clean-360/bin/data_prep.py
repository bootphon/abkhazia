# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
Data preparation LibriSpeech
Creating data for "train-clean-360" corpus
"""

import os
import subprocess
import re
import importlib
import logging
import sys
import shutil



#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################

#If generating the data for the first time, run all steps
#Otherwise, start from step 6 to just link the wavs rep. (wavs already available in /fhgfs/bootphon/data/derived_data/LibriSpeech_abkhazia/data/)


def list_dir(d):
    # filter out .DS_Store files from MacOS if any
    return [e for e in os.listdir(d) if e != '.DS_Store']


def list_LibriSpeech_files(raw_librispeech_path):
    """
    Return list of fullpaths to LibriSpeech files
    """
    file_list = []
    for dirpath, dirs, files in os.walk(raw_librispeech_path):
        for f in files:
              m_file = re.match("(.*)\.flac", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
                  print (f)
    return file_list


def flac_2_wav(flac_files, wav_dir, flac, exclude=None):
    """
    convert .flac (flac) files to .wav files
    
    flac_files is the list of full paths to the flac files
    to be converted to wavs

    wav_dir is the directory where the created wavs are put

    flac is the path to the flac executable

    exclude is a list of utt_id that shouldn't be used
    """
    if exclude is None:
        exclude = []
    if not(os.path.isdir(wav_dir)):
        os.mkdir(wav_dir)
    for inp in flac_files:
        bname = os.path.basename(inp)
        utt_id = bname.replace('.flac', '')
        if not(utt_id in exclude):  # exclude some utterances
            subprocess.call(flac + " -d -f {0}".format(inp), shell=True)
            wav_file = inp.replace ('.flac', '.wav')
            shutil.move(wav_file, wav_dir)


#STEP 5
def convert_speaker_ID_wav(i):
    """
    rename all wav_files to have "speaker_ID" of same length (add 0s at the beginning of speaker IDs)
    Argument is name of wav folder
    """
    for filename in os.listdir(i):
        filename_split = filename.split("-")
        speaker_ID = filename_split[0]
        old_file_path = os.path.join(i, filename)
        #speaker_ID shoud be XXXX - add as many "0"s at the beginning as necessary to get the correct length
        if (len(speaker_ID) == 2):
            new_filename = "00" + filename
            new_file_path = os.path.join(i, new_filename)
            os.rename(old_file_path, new_file_path)
        elif (len(speaker_ID) == 3):
            new_filename = "0" + filename
            new_file_path = os.path.join(i, new_filename)
            os.rename(old_file_path, new_file_path)
	print ('finished renaming wav files')
 
 

#STEP 4
#copy all transcription files to "derived data"
#Arguments are name of original transcription (i) and new transcription (o) folders
def copy_trs(i, o):
	input_dir = os.path.join(raw_librispeech_path, i)
	output_dir = os.path.join(derived_path, o)
	if not os.path.isdir(output_dir): 
		os.makedirs(output_dir)
	for dirpath, dirs, files in os.walk(input_dir):
		for filename in files:
			if filename.endswith('.txt'):
				shutil.copy2(os.path.join(dirpath, filename), output_dir)
	print ('finished moving all transcription files to transcription directory')




#STEP 7
#Create segments file: <utterance-id> <wav-filename>
#Create speakers file: <utterance-id> <speaker-id>
#Argument is name of wav directory
def segments_speakers(i):
	output_file_segment = os.path.join(output_dir, 'segments.txt')
	output_file_speaker = os.path.join(output_dir, 'utt2spk.txt')
	outfile1 = open(output_file_segment, "w")
	outfile2 = open(output_file_speaker, "w")
	input_dir = os.path.join(derived_path, i)
	files = os.listdir(input_dir)
	for filename in files:
		filename_split = filename.split("-")
		speaker_ID = filename_split[0]
		utt_ID = os.path.splitext(filename)[0]
		outfile1.write(utt_ID + ' ' + filename + '\n')
		outfile2.write(utt_ID + ' ' + speaker_ID + '\n')
	print ('finished creating segments and speakers files')


#STEP 8
#Create text file: <utterance-id> <word1> <word2> ... <wordn>
def text(trs, wav):
	new_wav_list = []
	output_file_text = os.path.join(output_dir, 'text.txt')
	output_corrupted_wavs = os.path.join(output_dir, 'corrupted_wavs.txt')
	outfile = open(output_file_text, "w")
	outfile2 = open(output_corrupted_wavs, "w")
	input_dir = os.path.join(derived_path, trs)
	if not os.path.isdir(input_dir): 
		os.makedirs(input_dir)
	input_dir_wav = os.path.join(derived_path, wav)
	files = os.listdir(input_dir)
	wav_list = os.listdir(input_dir_wav)
	#getting list of converted wav files (some files may be corrupted and might have not been converted and therefore their transcriptions must be discarded)
	for wav_file in wav_list:
		filename_no_ext = os.path.splitext(wav_file)[0]
		new_wav_list.append(filename_no_ext)
	for filename in files:
		infile = open(os.path.join(input_dir, filename), 'r')
		#for each line of transcript, convert the utt_ID to normalize speaker_ID and check if wav file exists;
		#if not, output corrputed files to corrupted_wavs.txt, else output text.txt
		for line in infile:
			m = re.match("([0-9\-]+)\s([A-Z].*)", line)
			if m:
				utterance_ID = m.group(1)
				utt = m.group(2)
				utterance_ID_split = utterance_ID.split("-")
				speaker_ID = utterance_ID_split[0]
				if (len(speaker_ID) == 2):
					new_utterance_ID = "00" + utterance_ID
					if (new_utterance_ID in new_wav_list):
						outfile.write(new_utterance_ID + ' ' + utt + '\n')
					else:
						outfile2.write(new_utterance_ID + '.wav\n')
				elif (len(speaker_ID) == 3):
					new_utterance_ID = "0" + utterance_ID
					if (new_utterance_ID in new_wav_list):
						outfile.write(new_utterance_ID + ' ' + utt + '\n')
					else:
						outfile2.write(new_utterance_ID + '.wav\n')
				else:
					if (utterance_ID in new_wav_list):
						outfile.write(utterance_ID + ' ' + utt + '\n')
					else:
						outfile2.write(new_utterance_ID + '.wav\n')
		infile.close()
	print ('finished creating text file')


#STEP 9
#Create lexicon file: <word> <phone_1> <phone_2> ... <phone_n>
def lexicon(i):
	dict_word = {}
	output_file_text = os.path.join(output_dir, 'lexicon.txt')
	output_file_text2 = os.path.join(output_dir, 'OOV.txt')
	outfile = open(output_file_text, "w")
	outfile2 = open(output_file_text2, "w")
	input_dir = os.path.join(derived_path, i)
	files = os.listdir(input_dir)
	for filename in files:
		infile = open(os.path.join(input_dir, filename), 'r')
		#for each line of transcription, store the words in a dictionary and increase frequency
		for line in infile:
			m = re.match("([0-9\-]+)\s([A-Z].*)", line)
			if m:
				utt = m.group(2)
				words = utt.split()
				for word in words:
					if word not in dict_word:
						dict_word[word] = 1
					else:
						dict_word[word] += 1
		infile.close()
	#To generate the lexicon, we will use the cmu dict and the dict of OOVs generated by LibriSpeech (available for download at http://www.openslr.org/11/)
	infile2 = open(os.path.join(raw_librispeech_path, 'librispeech-lexicon.txt'), 'r')
	infile3 = open(os.path.join(raw_cmu_path, 'cmudict.0.7a'), 'r')
	cmu_combined = {}
	for line in infile2:
		dictionary = re.match("(.*)\t(.*)", line)
		if dictionary:
			entry = dictionary.group(1)
			phn = dictionary.group(2)
			#remove pronunciation variants
			phn = phn.replace("0", "")
			phn = phn.replace("1", "")
			phn = phn.replace("2", "")
			#create the combined dictionary
			cmu_combined[entry] = phn;
	for line in infile3:
		dictionary = re.match("(.*)\s\s(.*)", line)
		if dictionary:
			entry = dictionary.group(1)
			phn = dictionary.group(2)
			#remove pronunciation variants
			phn = phn.replace("0", "")
			phn = phn.replace("1", "")
			phn = phn.replace("2", "")
			#create the combined dictionary
			cmu_combined[entry] = phn;
	infile2.close()
	infile3.close()
	#Loop through the words in transcripts by descending frequency and create the lexicon by looking up in the combined dictionary
	#if still OOV, output to OOV.txt
	for w, f in sorted(dict_word.items(), key=lambda kv: kv[1], reverse=True):
		if w in cmu_combined.viewkeys():
			outfile.write (w + ' ' + cmu_combined[w] + '\n')
		else:
			outfile2.write(w + '\t' + str(f) + '\n')
	print ('finished creating lexicon file')


#STEP 10
#copy phones file to data directory (should be distributed in Librispeech corpus) - will avoid us to look up for the associated IPA transcriptions
def copy_phones():
	subprocess.call("./copy_phones.sh", shell=True)
	print ('finished copying phones file')
 
 
#######################################################################################
#######################################################################################
##################################### Parameters ######################################
#######################################################################################
#######################################################################################

# Raw distribution of LibriSpeech is available at: http://www.openslr.org/12/
raw_librispeech_path = "/fhgfs/bootphon/data/raw_data/LibriSpeech/"

# path to CMU dictionary as available from http://www.speech.cs.cmu.edu/cgi-bin/cmudict (free)
# the recipe was designed using version 0.7a of the dictionary, but other recent versions
# could probably be used without changing anything 
raw_cmu_path = "/fhgfs/bootphon/data/raw_data/CMU_dict/"

# flac is required for converting .flac to .wav.
flac = "/usr/bin/flac"
#sph2pipe = "/Users/thomas/Documents/PhD/Recherche/kaldi/kaldi-trunk/tools/sph2pipe_v2.5/sph2pipe"
# Path to a directory where the processed corpora is to be stored

output_dir = "/fhgfs/bootphon/scratch/xcao/github_abkhazia/abkhazia/corpora/LibriSpeech_train-clean-360/"
#output_dir = "/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/corpora/WSJ_main_read"

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

LibriSpeech_flac = list_LibriSpeech_files(raw_librispeech_path)

"""
STEP 1 - copy all flac files into one flac directory to "derived data"
"""

#Running the different steps
#copy_flac ('train-clean-360','flac_train-clean-360')
#convert_flac()
#copy_trs ('train-clean-360','trs_train-clean-360')

#link_wavs()
#segments_speakers('wav_train-clean-360')
#text('trs_train-clean-360', 'wav_train-clean-360')
#lexicon('trs_train-clean-360')
#copy_phones()

#flac_files = list_LibriSpeech_files(raw_librispeech_path)
#flac_2_wav(flac_files, wav_dir, flac, exclude=None)
#convert_speaker_ID_wav (wav_dir)

	




