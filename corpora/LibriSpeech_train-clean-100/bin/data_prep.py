# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
Data preparation LibriSpeech
Creating data for "train-clean-100" corpus
"""

import os
import subprocess
import codecs
import re
import importlib
import logging
import shutil
import argparse
import sys



# paths - needs to change paths and versions of Librispeech
# create 'data' directory if doesn't exist
raw_path = "/fhgfs/bootphon/data/raw_data/LibriSpeech/"
dict_path = "/fhgfs/bootphon/data/raw_data/cmu_combined/"
derived_path = "/fhgfs/bootphon/data/derived_data/LibriSpeech_abkhazia/data/"
github_path = "/fhgfs/bootphon/scratch/xcao/github_abkhazia/abkhazia/corpora/LibriSpeech_train-clean-100/data/"


#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################

#If generating the data for the first time, run all steps
#Otherwise, start from step 6 to just link the wavs rep. (wavs already available in /fhgfs/bootphon/data/derived_data/LibriSpeech_abkhazia/data/)


#STEP 1
# filter out .DS_Store files from MacOS if any
def list_dir(d):
	return [e for e in os.listdir(d) if e != '.DS_Store']


#STEP 2
#copy all flac files into one flac directory to "derived data"
#Arguments are name of original flac (i) and new flac (o) folders
def copy_flac(i, o):
	input_dir = os.path.join(raw_path, i)
	output_dir = os.path.join(derived_path, o)
	if not os.path.isdir(output_dir): 
		os.makedirs(output_dir)
	for dirpath, dirs, files in os.walk(input_dir):
		for filename in files:
			if filename.endswith('.flac'):
				shutil.copy2(os.path.join(dirpath, filename), output_dir)
	print ('finished moving all flac files to flac directory')

#STEP 3
#call shell script to convert all flac files to wav files
def convert_flac():
	#needs to change path in convert_flac_wav.sh
	subprocess.call("./convert_flac_wav.sh", shell=True)
	print ('finished converting flac files to wav files and moving them to wav directory')

#STEP 4
#copy all transcription files to "derived data"
#Arguments are name of original transcription (i) and new transcription (o) folders
def copy_trs(i, o):
	input_dir = os.path.join(raw_path, i)
	output_dir = os.path.join(derived_path, o)
	if not os.path.isdir(output_dir): 
		os.makedirs(output_dir)
	for dirpath, dirs, files in os.walk(input_dir):
		for filename in files:
			if filename.endswith('.txt'):
				shutil.copy2(os.path.join(dirpath, filename), output_dir)
	print ('finished moving all transcription files to transcription directory')

#STEP 5
#rename all wav_files to have "speaker_ID" of same length (add 0s at the beginning of speaker IDs)
#Argument is name of wav folder
def convert_speaker_ID_wav(i):
	input_dir = os.path.join(derived_path, i)
	for filename in os.listdir(input_dir):
		filename_split = filename.split("-")
		speaker_ID = filename_split[0]
		old_file_path = os.path.join(input_dir, filename)
		#speaker_ID shoud be XXXX - add as many "0"s at the beginning as necessary to get the correct length
		if (len(speaker_ID) == 2):
			new_filename = "00" + filename
			new_file_path = os.path.join(input_dir, new_filename)
			os.rename(old_file_path, new_file_path)
		elif (len(speaker_ID) == 3):
			new_filename = "0" + filename
			new_file_path = os.path.join(input_dir, new_filename)
			os.rename(old_file_path, new_file_path)
	print ('finished renaming wav files')


#STEP 6
#link wav folder in the data kaldi directory
def link_wavs():
	subprocess.call("./link_wavs.sh", shell=True)
	print ('finished linking wavs directory and creating logs directory')


#STEP 7
#Create segments file: <utterance-id> <wav-filename>
#Create speakers file: <utterance-id> <speaker-id>
#Argument is name of wav directory
def segments_speakers(i):
	output_file_segment = os.path.join(github_path, 'segments.txt')
	output_file_speaker = os.path.join(github_path, 'utt2spk.txt')
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
	output_file_text = os.path.join(github_path, 'text.txt')
	output_corrupted_wavs = os.path.join(github_path, 'corrupted_wavs.txt')
	outfile = open(output_file_text, "w")
	outfile2 = open(output_corrupted_wavs, "w")
	input_dir = os.path.join(derived_path, trs)
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
	output_file_text = os.path.join(github_path, 'lexicon.txt')
	output_file_text2 = os.path.join(github_path, 'OOV.txt')
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
	infile2 = open(os.path.join(raw_path, 'librispeech-lexicon.txt'), 'r')
	infile3 = open(os.path.join(dict_path, 'cmudict.0.7a'), 'r')
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


#Running the different steps
copy_flac ('train-clean-100','flac_train-clean-100')
convert_flac()
copy_trs ('train-clean-100','trs_train-clean-100')
convert_speaker_ID_wav ('wav_train-clean-100')
link_wavs()
segments_speakers('wav_train-clean-100')
text('trs_train-clean-100', 'wav_train-clean-100')
lexicon('trs_train-clean-100')
copy_phones()
	




