# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Xuan-Nga Cao, Thomas Schatz
"""

"""
Data preparation WSJ for main corpus (excluding journalists) read speech
"""

#TODO besides, paths, needs to change regex to extract the correct files for appropriate corpus


import os
import subprocess
import re
import codecs

#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################


def list_dir(d):
    # filter out .DS_Store files from MacOS if any
	return [e for e in os.listdir(d) if e != '.DS_Store']


def list_wsj_files(raw_wsj_path, dir_filter, file_filter):
    """
    Return list of fullpaths to relevant WSJ files
    relevant being defined by dir_filter and file_filter. 
    See examples of usage below.
    """
    file_list = []
    for dirs_path, dirs, _ in os.walk(raw_wsj_path):
        for d in dirs:
            if dir_filter(d):
                for d_path, _, files in os.walk(os.path.join(dirs_path, d)):
                    for f in files:
                        if file_filter(f):
                            file_list.append(os.path.join(d_path, f))
    return file_list


def find_corrupted_utts(dot_files):
    bad_utts = []
    for f in dot_files:
        with codecs.open(f, mode='r', encoding='UTF-8') as inp:
            lines = inp.readlines()
        for line in lines:
            if "[bad_recording]" in line:
                # this tag in the transcript
                # indicates there is a problem
                # with the associated recording
                # (if it even exists)
                # so exclude it
                matches = re.match("(.*) \((.*)\)", line)
                utt_id = matches.group(2)
                bad_utts.append(utt_id)
    # could log the result...
    return bad_utts
    

def wv1_2_wav(wv1_files, wav_dir, sph2pipe, exclude=None):
    """
    convert .wv1 (flac) files to .wav files
    
    wv1_files is the list of full paths to the wv1 files
    to be converted to wavs

    wav_dir is the directory where the created wavs are put

    sph2pipe is the path to the sph2pipe executable

    exclude is a list of utt_id that shouldn't be used
    """
    if exclude is None:
        exclude = []
    if not(os.path.isdir(wav_dir)):
        os.mkdir(wav_dir)
    for inp in wv1_files:
        bname = os.path.basename(inp)
        utt_id = bname.replace('.wv1', '')
        if not(utt_id in exclude):  # exclude some utterances
            out = os.path.join(wav_dir, bname.replace('.wv1', '.wav'))
            subprocess.call(sph2pipe + " -f wav {0} >> {1}".format(inp, out), shell=True)


def make_utt_list(wav_dir, output_file):
    """
    create segments.txt 
    """
    files = list_dir(wav_dir)
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for f in files:
            assert '.wav' in f, \
                "file {0} in directory {1} is not a wavefile".format(f, wav_dir)
            utt_id = f.replace('.wav', '')
            out.write(u"{0} {1}\n".format(utt_id, f))


def make_spk_list(wav_dir, output_file):
    """
    create utt2spk.txt 
    """
    files = list_dir(wav_dir)   
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for f in files:
            assert '.wav' in f, \
                "file {0} in directory {1} is not a wavefile".format(f, wav_dir)
            utt_id = f.replace('.wav', '')
            # extract the first 3 characters from filename to get speaker_ID
            spk_id = f[:3]
            out.write(u"{0} {1}\n".format(utt_id, spk_id))


def rewrite_wsj_word(w):
    """
    return empty string to indicate that the word should be ignored
    """
    assert not w == "", "Empty word"
    w = w.upper()  # Upcase everything to match the CMU dictionary
    w = w.replace("\\", "")  # Remove backslashes.  We don't need the quoting
    w = w.replace("%PERCENT", "PERCENT")  # Normalization for Nov'93 test transcripts.
    w = w.replace(".POINT", "POINT")  # Normalization for Nov'93 test transcripts.
    if w[0] == "<" and w[-1] == ">": 
        # the <> means verbal deletion of a word.. but it's pronounced. (???)
        # we just remove the brackets
        w = w[1:-1]
    if w == "~":
        # "~" used to indicate truncation of an utterance. Not a word.
        return ""
    if w == ".":
        # "." used to indicate a pause, not included in the transcript for now. 
        # (could use a special SIL word in the dictionary for this)
        return ""
    if w[:1] == "[<" and w[-1] == "]":
        # E.g. [<door_slam], this means a door slammed in the preceding word.
        # we remove it from the transcript and keep the preceding word.
        # (could replace the preceding word by <NOISE>)
        return ""
    if w[0] == "[" and w[-2:] == ">]":
        # E.g. [door_slam>], this means a door slammed in the next word.
        # we remove it from the transcript and keep the next word.
        # (could replace the next word by <NOISE>)
        return ""
    if w[0] == "[" and w[-2:] == "/]":
        # E.g. [phone_ring/], which indicates the start of this phenomenon.
        # we remove it from the transcript and keep the part where the phone rings.
        # (could replace the whole part where the phone rings by <NOISE>)
        return ""
    if w[:1] == "[/" and w[-1] == "]":
        # E.g. [/phone_ring], which indicates the end of this phenomenon.
        # we remove it from the transcript and keep the part where the phone rings.
        # (could replace the whole part where the phone rings by <NOISE>)
        return ""
    if w[0] == "[" and w[-1] == "]":
        # Other noise indications, e.g. [loud_breath].
        # We replace them by the generic <NOISE> marker
        return "<noise>"
    if w == "--DASH":
        # This is a common issue; the CMU dictionary has it as -DASH.
        return "-DASH"
    # if we reached this point without returning, return w as is
    return w


def make_transcript(dot_files, output_file, exclude=None):
    """
    create text.txt from relevant WSJ dot_files
    """
    if exclude is None:
        exclude = []
    # read and concatenate content of all dot files
    lines = []
    for f in dot_files:
        with codecs.open(f, mode='r', encoding='UTF-8') as inp:
            lines = lines + inp.readlines()
    # parse each line and write it to output file in abkhazia format
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for line in lines:
            line = line.strip() # remove trailing spaces and newline characters
            # parse utt_id and text
            matches = re.match("(.*) \((.*)\)", line)
            text = matches.group(1)
            utt_id = matches.group(2)
            if utt_id in bad_utts:  # skip bad utterances                
                continue
            # correct some defect in original corpus (ad hoc)
            if utt_id == "400c0i2j":
                text = text.replace("  ", " ")
            # re-format text
            words = text.split(" ")
            words = [rewrite_wsj_word(w) for w in words]
            words = [w for w in words if w != ""]  # remove empty words
            text = " ".join(words)
            # output to file
            out.write(u"{0} {1}\n".format(utt_id, text))
   

def make_phones(phones, output_folder, silences=None, variants=None):
    """
    create phones.txt, variants.txt, silences.txt
    """
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
                

def make_lexicon(raw_cmu_path, output_file):
    """
    create lexicon.txt from CMU dictionary
    """
    with codecs.open(raw_cmu_path, mode='r', encoding='UTF-8') as inp:
        lines = inp.readlines()
    with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
        for line in lines:
            # remove newline and trailing spaces
            line = line.strip()
            # skip comments
            if len(line) >= 3 and line[:3] == u";;;":
                continue
            # parse line
            word, phones = line.split(u"  ")
            # skip alternative pronunciations,
            # the first one (with no parenthesized number at the end)
            # is supposed to be the most common and is retained
            if re.match(u"(.*)\([0-9]+\)$", word):
                continue
            # ignore stress variants of phones
            phones = re.sub(u"[0-9]+", u"", phones)
            # write to output file
            out.write(u"{0} {1}\n".format(word, phones))
        # add special word: <noise> NSN
        # special word <unk> SPN will be added automatically by validate_corpus
        # but it would make sense if to add it here if we used it for some
        # particular kind of noise, but this is not the case at present
        out.write(u"<noise> NSN\n")
     

#######################################################################################
#######################################################################################
##################################### Parameters ######################################
#######################################################################################
#######################################################################################

# path to raw LDC distribution of WSJ as available from https://catalog.ldc.upenn.edu/LDC93S6A 
# and https://catalog.ldc.upenn.edu/LDC94S13A (not free)
raw_wsj_path = "/fhgfs/bootphon/data/raw_data/WSJ_LDC/"
#raw_wsj_path = "/Users/thomas/Documents/PhD/Recherche/databases/WSJ_LDC/"
# path to CMU dictionary as available from http://www.speech.cs.cmu.edu/cgi-bin/cmudict (free)
# the recipe was designed using version 0.7a of the dictionary, but other recent versions
# could probably be used without changing anything 
raw_cmu_path = "/fhgfs/bootphon/data/raw_data/CMU_dict/cmudict.0.7a"
#raw_cmu_path = "/Users/thomas/Documents/PhD/Recherche/databases/CMU_dict/cmudict.0.7a"
# sph2pipe is required for converting .wv1 to .wav.
# One way to get it is to install kaldi, then sph2pipe can be found in:
#   /path/to/kaldi/tools/sph2pipe_v2.5/sph2pipe
sph2pipe = "/cm/shared/apps/kaldi/tools/sph2pipe_v2.5/sph2pipe"
#sph2pipe = "/Users/thomas/Documents/PhD/Recherche/kaldi/kaldi-trunk/tools/sph2pipe_v2.5/sph2pipe"
# Path to a directory where the processed corpora is to be stored
output_dir = "/fhgfs/bootphon/scratch/thomas/abkhazia/corpora/WSJ_main_read"
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


"""
STEP 0 - Listing relevant files for main_read part using the following 3 criterions:
    - these files are nested within one of the following directories: 
        si_tr_s, sd_tr_s, sd_tr_l (in WSJ0) and si_tr_s, si_tr_l (in WSJ1)
    - the 4 letter in the file name is 'c'
    - their extension is either .dot or .wv1 (transcriptions and recordings respectively)
"""
#TODO check if that's correct (in particular no sd_tr_s or l in WSJ1 and no si_tr_l in WSJ0 ??)
dir_filter = lambda d: d in ['si_tr_s', 'si_tr_l', 'sd_tr_s', 'sd_tr_l']
file_filter_dot = lambda f: f[3] == 'c' and f[-4:] == '.dot'
file_filter_wv1 = lambda f: f[3] == 'c' and f[-4:] == '.wv1'
main_read_wv1 = list_wsj_files(raw_wsj_path, dir_filter, file_filter_wv1)
main_read_dot = list_wsj_files(raw_wsj_path, dir_filter, file_filter_dot)


"""
STEP 1 - find corrupted utterances
"""
bad_utts = find_corrupted_utts(main_read_dot)
print("Found corrupted utterances")

"""
STEP 2 - Setting up wav folder
This step can take a lot of time (~70 000 files to convert)
"""
wv1_2_wav(main_read_wv1, wav_dir, sph2pipe, exclude=bad_utts)
print("Copied wavefiles")

"""
STEP 3 - segments.txt
"""
output_file = os.path.join(data_dir, "segments.txt")
make_utt_list(wav_dir, output_file)
print("Created segments.txt")

"""
STEP 4 - utt2spk.txt
"""
output_file = os.path.join(data_dir, "utt2spk.txt")
make_spk_list(wav_dir, output_file)
print("Created utt2spk.txt")

"""
STEP 5 - text.txt
"""
output_file = os.path.join(data_dir, "text.txt")
make_transcript(main_read_dot, output_file, exclude=bad_utts)
print("Created text.txt")

"""
STEP 6 - phones.txt, silences.txt, variants.txt
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

"""
STEP 7 - lexicon.txt
"""
output_file = os.path.join(data_dir, "lexicon.txt")
make_lexicon(raw_cmu_path, output_file)
print("Created lexicon.txt")
