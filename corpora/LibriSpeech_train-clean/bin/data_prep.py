# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
Data preparation LibriSpeech
Tested on "train-clean-100" and "train-clean-360" corpora
"""

import os
import subprocess
import re
import codecs
import shutil

"""
Change paths of your data in the "Parameters" section
"""

#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################

#If generating the data for the first time, run all steps
#Otherwise, start from step 2B (skip step 2A) to just link the wavs directory

"""
STEP 1
List all files and formats used in corpus
"""
def list_dir(d):
    # filter out .DS_Store files from MacOS if any
    return [e for e in os.listdir(d) if e != '.DS_Store']


#Get list of flacfiles
def list_flac(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.flac", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list

def list_trs(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.trans\.txt", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list

  
def list_wavs(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.wav$", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list 
    

"""
STEP 2A
Convert flac files to wav
"""

"""
    flac_files is the list of full paths to the flac files
    to be converted to wavs
    wav_dir is the directory where the created wavs are stored
    flac is the path to the flac executable
    exclude is a list of utt_id that shouldn't be used if any
"""
def flac_2_wav(flac_files, wav_dir, flac, exclude=None):
    if exclude is None:
        exclude = []
    if not(os.path.isdir(wav_dir)):
        os.mkdir(wav_dir)
    for inp in flac_files:
        print(inp)
        bname = os.path.basename(inp)
        utt_id = bname.replace('.flac', '')
        if not(utt_id in exclude):  # exclude some utterances
            #convert the inp file
            #-d is decode and by default will be in wav
            subprocess.call(flac + " -d -f {0}".format(inp), shell=True)
            wav_file = inp.replace ('.flac', '.wav')
            #move the wav file to the assigned directory
            shutil.move(wav_file, wav_dir)
    print ("converted all wav files")


"""
STEP 2B
Link speech folder to the data kaldi directory and also rename the wav files
to have "speaker_ID" of same length (add 0s at the beginning of speaker IDs)
"""
def link_wavs(wav_src, wav_dir, log_dir):
    input_wav = list_wavs(wav_src)
    if os.path.isdir(wav_dir):
        shutil.rmtree(wav_dir)
        os.makedirs(wav_dir)
        for wav_file in input_wav:
            bname = os.path.basename(wav_file)
            filename_split = bname.split("-")
            speaker_ID = filename_split[0]
            if (len(speaker_ID) == 2):
                new_filename = "00" + bname
                path_new_name = os.path.join(wav_dir, new_filename)
                os.symlink(wav_file, path_new_name)
            elif (len(speaker_ID) == 3):
                new_filename = "0" + bname
                path_new_name = os.path.join(wav_dir, new_filename)
                os.symlink(wav_file, path_new_name)
            else:
                path_new_name = os.path.join(wav_dir, bname)
                os.symlink(wav_file, path_new_name)
    print ('finished linking wav files')



"""
STEP 3
Create utterance files. It contains the list of all utterances with the name of the associated wavefiles,
and if there is more than one utterance per file, the start and end of the utterance in that wavefile expressed in seconds.
"segments.txt": <utterance-id> <wav-filename>
"""
def make_segment(wav_dir, output_file):
    outfile = open (output_file, "w")
    input_wav = list_wavs(wav_dir)
    for wav_file in input_wav:
        bname = os.path.basename(wav_file)
        utt_id = bname.replace('.wav', '')
        outfile.write(utt_id + ' ' + bname + '\n')
    print ('finished creating segments file')
    

"""
STEP 4
Create speaker file. It contains the list of all utterances with a unique identifier for the associated speaker.
"utt2spk.txt": <utterance-id> <speaker-id>
"""
def make_speaker(wav_dir, output_file):
    outfile = open (output_file, "w")
    input_wav = list_wavs(wav_dir)
    for wav_file in input_wav:
        bname = os.path.basename(wav_file)
        filename_split = bname.split("-")
        utt_id = bname.replace('.wav', '')
        speaker_id = filename_split[0]
        outfile.write(utt_id + ' ' + speaker_id + '\n')
    print ('finished creating utt2spk file')
    


"""
STEP 5
Create transcription file. It constains the transcription in word units for each utterance
"text.txt": <utterance-id> <word1> <word2> ... <wordn>
"""
def make_transcription(wav_dir, output_file, o_corrupted, input_dir):
    outfile = open(output_file, "w")
    outfile2 = open(o_corrupted, "w")
    wav_list = []
    input_wav = list_wavs(wav_dir)
    for wav_file in input_wav:
        bname = os.path.basename(wav_file)
        bname_no_ext = bname.replace('.wav', '')
        wav_list.append(bname_no_ext)
    input_trs = list_trs(input_dir)
    for filename in input_trs:
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
                    if (new_utterance_ID in wav_list):
                        outfile.write(new_utterance_ID + ' ' + utt + '\n')
                    else:
                        outfile2.write(new_utterance_ID + '.wav\n')
                elif (len(speaker_ID) == 3):
                    new_utterance_ID = "0" + utterance_ID
                    if (new_utterance_ID in wav_list):
                        outfile.write(new_utterance_ID + ' ' + utt + '\n')
                    else:
                        outfile2.write(new_utterance_ID + '.wav\n')
                else:
                    if (utterance_ID in wav_list):
                        outfile.write(utterance_ID + ' ' + utt + '\n')
                    else:
                        outfile2.write(utterance_ID + '.wav\n')
        infile.close()
    print ('finished creating text file')



"""
STEP 6
The phonetic dictionary contains a list of words with their phonetic transcription
Create phonetic dictionary file, "lexicon.txt": <word> <phone_1> <phone_2> ... <phone_n>
To do this, we need to get the mlfs for the language. Not sure it is available on the NCHLT website.
"""

def make_lexicon(i_libri_lex, i_cmu, outfile_lexicon):
    outfile = open(outfile_lexicon, "w")
    #To generate the lexicon, we will use the cmu dict and the dict of OOVs generated by LibriSpeech)
    infile = open(i_libri_lex, 'r')
    infile2 = open(i_cmu, 'r')
    cmu_combined = {}
    for line in infile:
        ignore_comment = re.match(";;; ", line)
        if ignore_comment:
            continue
        else:
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
        ignore_comment = re.match(";;; ", line)
        if ignore_comment:
            continue
        else:
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
    for w, f in sorted(cmu_combined.items()):
        outfile.write (w + ' ' + f + '\n')
    print ('finished creating lexicon file')
    outfile.close()



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
#raw_librispeech_path = "/media/xcao/data_CAO/cao/corpus_US/LibriSpeech/LibriSpeech_train-100/"
raw_librispeech_path = "/media/xcao/data_CAO/cao/corpus_US/LibriSpeech/LibriSpeech_train-360/"

# path to CMU dictionary as available from http://www.speech.cs.cmu.edu/cgi-bin/cmudict (free)
# the recipe was designed using version 0.7a of the dictionary, but other recent versions
# could probably be used without changing anything
# complementing with the LibriSpeech dict which contains the words not found in the cmu (not exhaustive list however)
# available for download at http://www.openslr.org/11/
raw_cmu_path = "/home/xcao/cao/corpus_US/CMU_dict/"
dict_librispeech_path = "/media/xcao/data_CAO/cao/corpus_US/LibriSpeech/"

# flac is required for converting .flac to .wav.
flac = "/usr/bin/flac"

# Path to a directory where the converted wav files will be stored
#wav_output_dir = "/media/xcao/data_CAO/cao/corpus_US/LibriSpeech/wavs_LibriSpeech_train-100/"
wav_output_dir = "/media/xcao/data_CAO/cao/corpus_US/LibriSpeech/wavs_LibriSpeech_train-360/"


# Path to a directory where the processed corpora is to be stored
output_dir = "/home/xcao/github_abkhazia/abkhazia/corpora/LibriSpeech_train-clean/"

#######################################################################################
#######################################################################################
###################################### Main part ######################################
#######################################################################################
#######################################################################################


# setting up some paths and directories
data_dir = os.path.join(output_dir, 'data')
if os.path.isdir(data_dir):
    shutil.rmtree(data_dir)
    os.makedirs(data_dir)
else:
    os.makedirs(data_dir)
wav_dir = os.path.join(data_dir, 'wavs')
if os.path.isdir(wav_dir):
    shutil.rmtree(wav_dir)
    os.makedirs(wav_dir)
else:
    os.makedirs(wav_dir)
log_dir = os.path.join(output_dir, 'logs')
if os.path.isdir(log_dir):
    shutil.rmtree(log_dir)
    os.makedirs(log_dir)
else:
    os.makedirs(log_dir)


"""
STEP 2A
Convert flac files to wav and also rename the wav files
"""
flac_files = list_flac(raw_librispeech_path)
flac_2_wav(flac_files, wav_output_dir, flac, exclude=None)


"""
STEP 2B
Link speech folder to the data kaldi directory
"""
link_wavs(wav_output_dir, wav_dir, log_dir)


"""
STEP 3
Create utterance files. It contains the list of all utterances with the name of the associated wavefiles,
and if there is more than one utterance per file, the start and end of the utterance in that wavefile expressed in seconds.
"segments.txt": <utterance-id> <wav-filename>
"""
output_file = os.path.join(data_dir, 'segments.txt')
wav_dir = os.path.join(data_dir, 'wavs')
make_segment(wav_dir, output_file)


"""
STEP 4
Create speaker file. It contains the list of all utterances with a unique identifier for the associated speaker.
"utt2spk.txt": <utterance-id> <speaker-id>
"""
output_file = os.path.join(data_dir, 'utt2spk.txt')
wav_dir = os.path.join(data_dir, 'wavs')
make_speaker(wav_dir, output_file)


"""
STEP 5
Create transcription file. It constains the transcription in word units for each utterance
"text.txt": <utterance-id> <word1> <word2> ... <wordn>
"""
output_file_text = os.path.join(data_dir, 'text.txt')
output_corrupted_wavs = os.path.join(log_dir, 'corrupted_wavs.txt')
make_transcription(wav_dir, output_file_text, output_corrupted_wavs, raw_librispeech_path)


"""
STEP 6
The phonetic dictionary contains a list of words with their phonetic transcription
Create phonetic dictionary file, "lexicon.txt": <word> <phone_1> <phone_2> ... <phone_n>
"""
infile_libri_lex = os.path.join(dict_librispeech_path, 'librispeech-lexicon.txt')
infile_cmu = os.path.join(raw_cmu_path, 'cmudict.0.7a')
output_file_text = os.path.join(data_dir, 'lexicon.txt')
make_lexicon(infile_libri_lex, infile_cmu, output_file_text)


"""
STEP 7
The phone inventory contains a list of each symbol used in the pronunciation dictionary
Create phone list file, "phones.txt": <phone-symbol> <ipa-symbol>
# get IPA transcriptions for all phones
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