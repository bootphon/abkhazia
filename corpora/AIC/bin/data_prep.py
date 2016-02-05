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
import subprocess
import codecs


#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################

"""
STEP 1
List all files and formats used in corpus
"""
def list_dir(d):
	return [e for e in os.listdir(d) if e != '.DS_Store']

#Get list of flac files
def list_flac(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.flac", f)
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
def link_wavs(wav_path_src, wav_dir, log_dir):
    #if folder already exists and has link, unlink and recreate link
    if os.path.isdir(wav_dir):
        if os.path.islink(wav_dir):
            os.unlink(wav_dir)
            os.symlink(wav_path_src, wav_dir)
        #if folder already exists and is unlinked, remove folder and re-create symbolic link
        else:
            shutil.rmtree(wav_dir)
            os.symlink(wav_path_src, wav_dir)
    #if wavs folder doesn't exist, create symbolic link to speech data
    else:
        os.symlink(wav_path_src, wav_dir)
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
        filename_split = bname.split("_")
        utt_id = bname.replace('.wav', '')
        speaker_id = filename_split[0]
        outfile.write(utt_id + ' ' + speaker_id + '\n')
    print ('finished creating utt2spk file')



"""
STEP 5
Create transcription file. It constains the transcription in word units for each utterance
"text.txt": <utterance-id> <word1> <word2> ... <wordn>
"""
def make_transcription(input_file1, input_file2, output_file):
    infile1 = open(input_file1, "r")
    infile2 = open(input_file2, "r")
    outfile = open(output_file, "w")
    for line in infile1:
            outfile.write(line)
    for line in infile2:
            outfile.write(line)
    print ('finished creating text file')
    infile1.close()
    infile2.close()
    outfile.close()
    


"""
STEP 6
The phonetic dictionary contains a list of words with their phonetic transcription
Create phonetic dictionary file, "lexicon.txt": <word> <phone_1> <phone_2> ... <phone_n>
"""
#Create temp lexicon file and temp OOVs
#No transcription for the words, we will use the CMU but will need to convert to the symbols used in the AIC
def temp_cmu_lexicon(in_cmu, in_text, out_temp_lex, out_OOV):
    dict_word = {}
    cmu_dict = {}
    infile = open(in_cmu, "r")
    infile2 = open (in_text, "r")
    outfile = open(out_temp_lex, "w")
    outfile2 = open(out_OOV, "w")
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
    print ('finished creating temp lexicon file')
    


def make_lexicon(in_temp_lex, in_OOV, output_file_text):
    array_phn = []
    infile = open(in_temp_lex, "r")
    infile2 = open (in_OOV, "r")
    outfile = open(output_file_text, "w")
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
                print(sound)
    infile.close()
    infile2.close()
    print ('finished creating lexicon file')
    outfile.close()
    #remove the temp files
    os.remove(in_temp_lex)
    os.remove(in_OOV)



"""
STEP 7
The phone inventory contains a list of each symbol used in the pronunciation dictionary
Create phone list file, "phones.txt": <phone-symbol> <ipa-symbol>
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

# Distribution of the revised AIC corpus is freely available at LDC: https://catalog.ldc.upenn.edu/LDC2015S12
# However, you need to be signed in as an organization to add the corpus to the cart.
# If you are an individual, sign up for an account but you need to click on "create your organization" on the registration page
# to add your organization and have administration privileges.

raw_AIC_path = "/home/xcao/cao/corpus_US/AI_corpus/articulation_index_lcsp"

# flac is required for converting .flac to .wav.
flac = "/usr/bin/flac"


# path to CMU dictionary as available from http://www.speech.cs.cmu.edu/cgi-bin/cmudict (free)
# the recipe was designed using version 0.7a of the dictionary, but other recent versions
# could probably be used without changing anything
# complementing with the LibriSpeech dict which contains the words not found in the cmu (not exhaustive list however)
# available for download at http://www.openslr.org/11/
raw_cmu_path = "/home/xcao/cao/corpus_US/CMU_dict/"

# Path to a directory where the converted wav files will be stored
wav_output_dir = "/home/xcao/cao/corpus_US/AI_corpus/wav_AI_lscp"

# Path to a directory where the processed corpora is to be stored
output_dir = "/home/xcao/github_abkhazia/abkhazia/corpora/AIC/"


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
log_dir = os.path.join(output_dir, 'logs')
if not os.path.isdir(log_dir):
    os.makedirs(log_dir)


"""
STEP 2A
Convert flac files to wav and copy the wav files
"""
#flac_files = list_flac(raw_AIC_path)
#flac_2_wav(flac_files, wav_output_dir, flac, exclude=None)


"""
STEP 2B
Link speech folder to the data kaldi directory
"""
#link_wavs(wav_output_dir, wav_dir, log_dir)


"""
STEP 3
Create utterance files. It contains the list of all utterances with the name of the associated wavefiles,
and if there is more than one utterance per file, the start and end of the utterance in that wavefile expressed in seconds.
"segments.txt": <utterance-id> <wav-filename>
"""
#output_file = os.path.join(data_dir, 'segments.txt')
#wav_dir = os.path.join(data_dir, 'wavs')
#make_segment(wav_dir, output_file)


"""
STEP 4
Create speaker file. It contains the list of all utterances with a unique identifier for the associated speaker.
"utt2spk.txt": <utterance-id> <speaker-id>
"""
#output_file = os.path.join(data_dir, 'utt2spk.txt')
#wav_dir = os.path.join(data_dir, 'wavs')
#make_speaker(wav_dir, output_file)


"""
STEP 5
Create transcription file. It constains the transcription in word units for each utterance
"text.txt": <utterance-id> <word1> <word2> ... <wordn>
"""
#input_file1 = os.path.join(raw_AIC_path, 'data/text/normal.txt')
#input_file2 = os.path.join(raw_AIC_path, 'data/text/weird.txt')
#output_file_text = os.path.join(data_dir, 'text.txt')
#make_transcription(input_file1, input_file2, output_file_text)



"""
STEP 6
The phonetic dictionary contains a list of words with their phonetic transcription
Create phonetic dictionary file, "lexicon.txt": <word> <phone_1> <phone_2> ... <phone_n>
"""
#cmu_infile = os.path.join(raw_cmu_path, 'cmudict.0.7a')
#text_infile = os.path.join(data_dir, 'text.txt')
#out_temp_lex = os.path.join(log_dir, 'temp_lexicon_cmu.txt')
#out_OOV = os.path.join(log_dir, 'temp_OOV.txt')
#temp_cmu_lexicon(cmu_infile, text_infile, out_temp_lex, out_OOV)


#in_temp_lex = os.path.join(log_dir, 'temp_lexicon_cmu.txt')
#in_OOV = os.path.join(log_dir, 'temp_OOV.txt')
#output_file_text = os.path.join(data_dir, 'lexicon.txt')
#make_lexicon (in_temp_lex, in_OOV, output_file_text)



"""
STEP 7
The phone inventory contains a list of each symbol used in the pronunciation dictionary
Create phone list file, "phones.txt": <phone-symbol> <ipa-symbol>
# get IPA transcriptions for all phones
"""
AIC_phones = [
    ('a', u'ɑː'),
    ('xq', u'æ'),
    ('xa', u'ʌ'),
    ('c', u'ɔː'),
    ('xw', u'aʊ'),
    ('xy', u'aɪ'),
    ('xr', u'ɝ'),
    ('xe', u'ɛ'),
    ('e', u'eɪ'),
    ('xi', u'ɪ'),
    ('i', u'iː'),
    ('o', u'oʊ'),
    ('xo', u'ɔɪ'),
    ('xu', u'ʊ'),
    ('u', u'uː'),
    ('b', u'b'),
    ('xc', u'ʧ'),
    ('d', u'd'),
    ('xd', u'ð'),
    ('f', u'f'),
    ('g', u'g'),
    ('h', u'h'),
    ('xj', u'ʤ'),
    ('k', u'k'),
    ('l', u'l'),
    ('m', u'm'),
    ('n', u'n'),
    ('xg', u'ŋ'),
    ('p', u'p'),
    ('r', u'r'),
    ('s', u's'),
    ('xs', u'ʃ'),
    ('t', u't'),
    ('xt', u'θ'),
    ('v', u'v'),
    ('w', u'w'),
    ('y', u'j'),
    ('z', u'z'),
    ('xz', u'ʒ'),
]
phones = {}
for phone, ipa in AIC_phones:
    phones[phone] = ipa
silences = [u"NSN"]  # SPN and SIL will be added automatically
variants = []  # could use lexical stress variants...
make_phones(phones, data_dir, silences, variants)
print("Created phones.txt, silences.txt, variants.txt")

