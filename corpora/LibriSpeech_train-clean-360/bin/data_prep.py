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
import codecs
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


"""
Return list of fullpaths for flac files in LibriSpeech 
"""
def list_LibriSpeech_flac_files(raw_librispeech_path):
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

    exclude is a list of utt_id that shouldn't be used if any
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



"""
rename all wav_files to have "speaker_ID" of same length (add 0s at the beginning of speaker IDs)
Argument is name of wav folder
"""
def convert_speaker_ID_wav(i):
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



"""
Create segments file: <utterance-id> <wav-filename>
Create speakers file: <utterance-id> <speaker-id>
"""
def make_segments_speakers(i, o_segments, o_speakers):
    
    outfile1 = open(o_segments, "w")
    outfile2 = open(o_speakers, "w")
    files = os.listdir(i)
    for filename in files:
        filename_split = filename.split("-")
        speaker_ID = filename_split[0]
        utt_ID = os.path.splitext(filename)[0]
        outfile1.write(utt_ID + ' ' + filename + '\n')
        outfile2.write(utt_ID + ' ' + speaker_ID + '\n')
    outfile1.close()
    outfile2.close()
    print ('finished creating segments and speakers files')



"""
Return list of fullpaths for trs files in LibriSpeech
"""
def list_LibriSpeech_trs_files(raw_librispeech_path):
    file_list = []
    for dirpath, dirs, files in os.walk(raw_librispeech_path):
        for f in files:
              m_file = re.match("(.*)\.txt", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
                  print (f)
    return file_list



"""
Create text file: <utterance-id> <word1> <word2> ... <wordn>
"""
def make_transcript(i, o_text, o_corrupted, trs_files):
	new_wav_list = []
	outfile = open(o_text, "w")
	outfile2 = open(o_corrupted, "w")
	wav_list = os.listdir(i)
	#getting list of converted wav files (some files may be corrupted and might have not been converted and therefore their transcriptions must be discarded)
	for wav_file in wav_list:
		filename_no_ext = os.path.splitext(wav_file)[0]
		new_wav_list.append(filename_no_ext)
	for filename in trs_files:
		infile = open(filename, 'r')
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



"""
Create lexicon file: <word> <phone_1> <phone_2> ... <phone_n>
"""
def make_lexicon(i_libri_lex, i_cmu, o_lex, o_OOV, trs_files):
	dict_word = {}
	outfile = open(o_lex, "w")
	outfile2 = open(o_OOV, "w")
	for filename in trs_files:
		infile = open(filename, 'r')
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
	infile = open(i_libri_lex, 'r')
	infile2 = open(i_cmu, 'r')
	cmu_combined = {}
	for line in infile:
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
	for line in infile2:
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
	infile.close()
	infile2.close()
	#Loop through the words in transcripts by descending frequency and create the lexicon by looking up in the combined dictionary
	#if still OOV, output to OOV.txt
	for w, f in sorted(dict_word.items(), key=lambda kv: kv[1], reverse=True):
		if w in cmu_combined.viewkeys():
			outfile.write (w + ' ' + cmu_combined[w] + '\n')
		else:
			outfile2.write(w + '\t' + str(f) + '\n')
	print ('finished creating lexicon file')
	outfile.close()
	outfile2.close()



"""
Create phones.txt, variants.txt, silences.txt
"""
def make_phones(phones, output_folder, silences=None, variants=None):
    # code taken from GP_Mandarin... could share it ?
    output_file = os.path.join(output_folder, 'phones.txt') 
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for phone in phones:
            out.write(u"{0} {1}\n".format(phone, phones[phone]))
    if not(silences is None):
        output_file = os.path.join(output_folder, 'silences.txt')
        with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
            for sil in silences:
                out.write(sil + u"\n")
    if not(variants is None):
        output_file = os.path.join(output_folder, 'variants.txt')
        with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
            for l in variants:
                out.write(u" ".join(l) + u"\n")
                
  
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

# Path to a directory where the processed corpora is to be stored
output_dir = "/fhgfs/bootphon/scratch/xcao/abkhazia/corpora/LibriSpeech_train-clean-360/"

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


"""
STEP 1 - Setting up wav folder
This step can take a lot of time
"""
#flac_files = list_LibriSpeech_flac_files(raw_librispeech_path)
#flac_2_wav(flac_files, wav_dir, flac, exclude=None)
#convert_speaker_ID_wav (wav_dir)
#print("Converted wavefiles")


"""
STEP 2 - segments.txt and utt2spk.txt
"""
#output_file_segments = os.path.join(data_dir, "segments.txt")
#output_file_speakers = os.path.join(data_dir, "utt2spk.txt")
#make_segments_speakers(wav_dir, output_file_segments, output_file_speakers)
#print("Created segments and utt2spk.txt")


"""
STEP 3 - text.txt
"""
#trs_files = list_LibriSpeech_trs_files(raw_librispeech_path)
#output_file_text = os.path.join(data_dir, 'text.txt')
#output_corrupted_wavs = os.path.join(data_dir, 'corrupted_wavs.txt')
#make_transcript(wav_dir, output_file_text, output_corrupted_wavs, trs_files)
#print("Created text.txt")


"""
STEP 4 - lexicon.txt
"""
#trs_files = list_LibriSpeech_trs_files(raw_librispeech_path)
#infile_libri_lex = os.path.join(raw_librispeech_path, 'librispeech-lexicon.txt')
#infile_cmu = os.path.join(raw_cmu_path, 'cmudict.0.7a')
#output_file_text = os.path.join(data_dir, 'lexicon.txt')
#output_file_text2 = os.path.join(data_dir, 'OOV.txt')
#make_lexicon(infile_libri_lex, infile_cmu, output_file_text, output_file_text2, trs_files)
#print("Created lexicon.txt")


"""
STEP 5 - phones.txt, silences.txt, variants.txt
    using the CMU phoneset without lexical stress
    variants and with a special NSN phone for
    various kind of noises
"""

CMU_phones = [
    ('IY', u'iː'),
    ('IH', u'ɪ'),
    ('EH', u'ɛ'),
    ('EY', u'eɪ'),
    ('AE', u'æ'),
    ('AA', u'ɑː'),
    ('AW', u'aʊ'),
    ('AY', u'aɪ'),
    ('AH', u'ʌ'),
    ('AO', u'ɔː'),
    ('OY', u'ɔɪ'),
    ('OW', u'oʊ'),
    ('UH', u'ʊ'),
    ('UW', u'uː'),
    ('ER', u'ɝ'),
    ('JH', u'ʤ'),
    ('CH', u'ʧ'),
    ('B', u'b'),
    ('D', u'd'),
    ('G', u'g'),
    ('P', u'p'),
    ('T', u't'),
    ('K', u'k'),
    ('S', u's'),
    ('SH', u'ʃ'),
    ('Z', u'z'),
    ('ZH', u'ʒ'),
    ('F', u'f'),
    ('TH', u'θ'),
    ('V', u'v'),
    ('DH', u'ð'),
    ('M', u'm'),
    ('N', u'n'),
    ('NG', u'ŋ'),
    ('L', u'l'),
    ('R', u'r'),
    ('W', u'w'),
    ('Y', u'j'),
    ('HH', u'h')
]
phones = {}
for phone, ipa in CMU_phones:
    phones[phone] = ipa
silences = [u"NSN"]  # SPN and SIL will be added automatically
variants = []  # could use lexical stress variants...
make_phones(phones, data_dir, silences, variants)
print("Created phones.txt, silences.txt, variants.txt")