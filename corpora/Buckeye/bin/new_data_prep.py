# -*- coding: utf-8 -*-
"""
Data preparation for Buckeye

@author: Roland Thiolliere
"""

import os
import codecs
import re
import os.path as path
import shutil

#Get list of wav files
def list_wavs(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.wav$", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list

#Get list of word files
def list_wrds(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.wrd$", f)
              if m_file:
                  file_list.append(os.path.join(dirpath, f))
    return file_list
    
#Get list of txt files
def list_utts(input_dir):
    file_list = []
    for dirpath, dirs, files in os.walk(input_dir):
        for f in files:
              m_file = re.match("(.*)\.txt$", f)
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
    for utts in input_txt:
        length_utt = []
        with open (utts) as infile_txt:
            current_index = 0
            lines = infile_txt.readlines()
            bname = os.path.basename(utts)
            bname_word = bname.replace('txt', 'wrd')
            bname_wav = bname.replace('txt', 'wav')
            utt = bname.replace('.txt', '')
            length_utt = [len(line.strip().split()) for line in lines]
            wrd = os.path.join(wrd_dir, bname_word)
            with open (wrd) as infile_wrd:
                lines_2 = infile_wrd.readlines()
                assert len(lines_2) == sum(length_utt), '{} {}'.format(len(lines_2), sum(length_utt))
                if (len(length_utt) == 1):
                    #print (utts)
                    match_onset = re.match('(.*)\t(.*)\t(.*)', lines_2[0])
                    if not match_onset:
                        raise IOError
                    onset = match_onset.group(1)
                    match_offset = re.match('(.*)\t(.*)\t(.*)', lines_2[-1])
                    if not match_offset:
                        raise IOError
                    offset = match_offset.group(2)
                    outfile.write(utt + '-sent1' + ' ' + bname_wav + ' ' + str(onset) + ' ' + str(offset) + '\n')
                else:
                    for n in range(len(length_utt)):
                        if (n == 0):
                            onset_line = str(lines_2[n])
                            match_onset = re.match('(.*)\t(.*)\t(.*)', onset_line)
                            if not match_onset:
                                raise IOError
                            onset = match_onset.group(1)
                            outfile.write(utt + '-sent' + str(n+1) + ' ' + bname_wav + ' ' + str(onset) + ' ')
    
                            index_offset = length_utt[n]
                            offset_line = lines_2[index_offset]
                            match_offset = re.match('(.*)\t(.*)\t(.*)', offset_line)
                            if not match_offset:
                                raise IOError
                            offset = match_offset.group(1)
                            outfile.write(str(offset))
                            current_index = index_offset
                            outfile.write('\n')
                        else:
                            onset_line = str(lines_2[current_index])
                            match_onset = re.match('(.*)\t(.*)\t(.*)', onset_line)
                            if not match_onset:
                                raise IOError
                            onset = match_onset.group(1)
                            outfile.write(utt + '-sent' + str(n+1) + ' ' + bname_wav + ' ' + str(onset) + ' ')
                            index_offset = length_utt[n]+current_index
                            offset_line = lines_2[index_offset-1]
                            match_offset = re.match('(.*)\t(.*)\t(.*)', offset_line)
                            if not match_offset:
                                raise IOError
                            offset = match_offset.group(2)
                            outfile.write(str(offset))
                            current_index = index_offset
                            outfile.write('\n')
    print ('finished creating segments file')



def spk_list(segment_file, output_file):
    """
    Maps each utterance to the corresponding speaker
    """
    outfile = open(output_file, 'w')
    with codecs.open(segment_file, mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()
        for l in lines:
            match = re.match('(.*)\s(.*)\s(.*)\s(.*)\s(.*)', l)
            if not match:
                raise IOError
            utt_ID = match.group(1)
            speaker_ID = utt_ID[:3]
            outfile.write(utt_ID + ' ' + speaker_ID + '\n')
    print ('finished creating utt2spk file')
            

def extract_transcript(input_dir, output_file):
    """
    Write the text transcription for each utterance
    <utterance-id> <word1> <word2> ... <wordn>
    """
    outfile = open (output_file, "w")
    input_txt = list_utts(input_dir)
    for utts in input_txt:
        n = 1
        lines = [line.rstrip('\n') for line in open(utts)]
        bname = os.path.basename(utts)
        utt = bname.replace('.txt', '')
        for l in lines:
            outfile.write(utt + '-sent' + str(n) + ' ' + l + '\n')
            n = n+1
    print ('finished creating text file')
            
            
def make_lexicon(input_dir, output_file):
    dict_word = {}
    outfile = open (output_file, "w")
    input_txt = list_wrds(input_dir)
    for utts in input_txt:
        with open (utts) as infile_txt:
            #for each line of transcription, store the words in a dictionary and increase frequency
            lines = infile_txt.readlines()
            for line in lines:
                line.strip()
                format_match = re.match("(.*)\t(.*)\t(.*)", line)
                if format_match:
                    word_trs = format_match.group(3)
                    word_format_match = re.match("(.*); (.*); (.*); (.*)", word_trs)
                    if word_format_match:
                        word = word_format_match.group(1)
                        phn_trs = word_format_match.group(3)
                        if word == "<UNKNOWN>":
                            phn_trs = phn_trs.replace('UNKNOWN', 'SPN')
                        elif word == "<UNKNOWN_WW>":
                            phn_trs = phn_trs.replace('UNKNOWN_WW', 'SPN')
                        elif word == "<CUTOFF>":
                            phn_trs = phn_trs.replace('CUTOFF', 'SPN')
                        if word not in dict_word:
                            dict_word[word] = phn_trs
    for w, f in sorted(dict_word.items(), key=lambda kv: kv[1], reverse=True):
        outfile.write (w + ' ' + f + '\n')
    print ('finished creating lexicon file')
    

   
def phone_list(wrd_files):
    """
    Defines phone inventory
    """
    phns = []
    phn_dict = {}
    for inp in wrd_files:
        infile = open(inp, 'r')
        lines = infile.readlines()
        for line in lines:
            line.strip()
            format_match = re.match("(.*)\t(.*)\t(.*)", line)
            if format_match:
                word_trs = format_match.group(3)
                word_format_match = re.match("(.*); (.*); (.*); (.*)", word_trs)
                if word_format_match:
                    phn_trs = word_format_match.group(3)
                    phns = phn_trs.split()
                    for p in phns:
                        #if p == "U":
                            #print(inp+line)
                        if p in phn_dict:
                            phn_dict[p] += 1
                        else:
                            phn_dict[p] = 1
    return phn_dict.keys()


def write_phone(phones, output_file, output_file2):
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for phone in phones:
            out.write(u"{0} {1}\n".format(phone, phones[phone]))
    with codecs.open(output_file2, mode='w', encoding='UTF-8') as out2:
        out2.write('SIL\n')
        out2.write('SIL_WW\n')
    print ('finished creating phones file')


# get IPA transcriptions
Buckeye_phones = [
    ('iy', u'iː'),
    ('ih', u'ɪ'),
    ('eh', u'ɛ'),
    ('ey', u'eɪ'),
    ('ae', u'æ'),
    ('aa', u'ɑː'),
    ('aw', u'aʊ'),
    ('ay', u'aɪ'),
    ('ah', u'ʌ'),
    ('ao', u'ɔː'),
    ('oy', u'ɔɪ'),
    ('ow', u'oʊ'),
    ('uh', u'ʊ'),
    ('uw', u'uː'),
    ('er', u'ɝ'),
    ('jh', u'ʤ'),
    ('ch', u'ʧ'),
    ('b', u'b'),
    ('d', u'd'),
    ('g', u'g'),
    ('p', u'p'),
    ('t', u't'),
    ('k', u'k'),
    ('dx', u'ɾ'),
    ('s', u's'),
    ('sh', u'ʃ'),
    ('z', u'z'),
    ('zh', u'ʒ'),
    ('f', u'f'),
    ('th', u'θ'),
    ('v', u'v'),
    ('dh', u'ð'),
    ('m', u'm'),
    ('n', u'n'),
    ('ng', u'ŋ'),
    ('em', u'm\u0329'),
    ('nx', u'ɾ\u0303'),
    ('en', u'n\u0329'),
    ('eng', u'ŋ\u0329'),
    ('l', u'l'),
    ('r', u'r'),
    ('w', u'w'),
    ('y', u'j'),
    ('hh', u'h'),
    ('el', u'l\u0329'),
    ('tq', u'ʔ'),
    ('B', u'B'),
    ('E', u'E'),
    ('ahn', u'ʌ\u0329'),
    ('iyn', u'iː\u0329'),
    ('eyn', u'eɪ\u0329'),
    ('oyn', u'ɔɪ\u0329'),
    ('ehn', u'ɛ\u0329'),
    ('uhn', u'ʊ\u0329'),
    ('ayn', u'aɪ\u0329'),
    ('own', u'oʊ\u0329'),
    ('awn', u'aʊ\u0329'),
    ('aon', u'ɔː\u0329'),
    ('aan', u'ɑː\u0329'),
    ('ihn', u'ɪ\u0329'),
    ('ern', u'ɝ\u0329'),
    ('uwn', u'uː\u0329'),
    ('aen', u'æ\u0329'),
    ('aan', u'ɑː\u0329'),
    ('ERROR', u'ERROR'),
    ('EXCLUDE', u'EXCLUDE'),
    ('UNKNOWN_WW', u'UNKNOWN_WW'),
    ('VOCNOISE', u'VOCNOISE'),
    ('HESITATION_TAG', u'HESITATION_TAG'),
    ('LENGTH_TAG', u'LENGTH_TAG'),
    ('VOCNOISE_WW', u'VOCNOISE_WW'),
    ('NOISE', u'NOISE'),
    ('NOISE_WW', u'NOISE_WW'),
    ('IVER', u'IVER'),
    ('LAUGH', u'LAUGH'),
    ('HESITATION_TAG', u'HESITATION_TAG'),
]

#######################################################################################
#######################################################################################
##################################### Parameters ######################################
#######################################################################################
#######################################################################################

# Raw distribution of LibriSpeech is available at: http://www.openslr.org/12/
raw_buckeye_path = "/home/xcao/cao/corpus_US/BUCKEYE/Buckeye_final_check"
buckeke_path_with_foldings = "/home/xcao/cao/corpus_US/BUCKEYE/test_buckeye"

# path to CMU dictionary as available from http://www.speech.cs.cmu.edu/cgi-bin/cmudict (free)
# the recipe was designed using version 0.7a of the dictionary, but other recent versions
# could probably be used without changing anything
# complementing with the LibriSpeech dict which contains the words not found in the cmu (not exhaustive list however)
# available for download at http://www.openslr.org/11/
# raw_cmu_path = "/fhgfs/bootphon/data/raw_data/CMU_dict/"

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


"""
STEP 2 - segments.txt
"""
output_file = os.path.join(data_dir, 'segments.txt')
utt_dir = os.path.join(raw_buckeye_path, 'orig_txt_adjusted')
wrd_dir = os.path.join(buckeke_path_with_foldings, 'wrd_with_foldings')
#wrd_dir = os.path.join(raw_buckeye_path, 'wrd')
extract_utt(utt_dir, output_file)


"""
STEP 3 - utt2spk.txt
"""
segment_file = os.path.join(data_dir, 'segments.txt')
output_file = os.path.join(data_dir, 'utt2spk.txt')
spk_list(segment_file, output_file)

"""
STEP 4 - text.txt
"""
utt_dir = os.path.join(buckeke_path_with_foldings, 'txt_with_foldings')
output_file = os.path.join(data_dir, 'text.txt')
extract_transcript(utt_dir, output_file)

"""
STEP 5 - lexicon.txt
"""
output_file = os.path.join(data_dir, 'lexicon.txt')
wrd_dir = os.path.join(buckeke_path_with_foldings, 'wrd_with_foldings')
make_lexicon(wrd_dir, output_file)

"""
STEP 6 - phones.txt
"""
wrd_files = list_wrds(os.path.join(buckeke_path_with_foldings, 'wrd_with_foldings'))
phoneset = set(phone_list(wrd_files))
phones = {}
for phone in phoneset:
	for p, ipa in Buckeye_phones:
		if p == phone:
			phones[phone] = ipa
write_phone(phones, os.path.join(data_dir, 'phones.txt'), os.path.join(data_dir, 'silences.txt'))

