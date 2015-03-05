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


class Buckeye(object):
    root = '/fhgfs/bootphon/scratch/roland/abkhazia/corpora/buckeye'

    paths = {
        'wavs': path.join(root, 'data/wavs'),
        'utt_list': path.join(root, 'data/segments'),
        'spk_list': path.join(root, 'data/utt2spk'),
        'phones': path.join(root, 'data/phones.txt'),
        'text': path.join(root, 'data/text'),
        'silences': path.join(root, 'data/silences.txt'),
        'dict': path.join(root, 'data/lexicon.txt')
        }


    def Buckeye(self, input_dir, paths, verbose=1):
        self.wav_files = extract_wav(input_dir, paths['wavs'])
        self.wrd_files = list_wrds(input_dir)
        self.utts = {path.basename(wrd_file): extract_utt(wrd_file)
                     for wrd_file in self.wrd_files}
        self.extended_utts = utt_list(self.utts, self.wav_files, paths['utt_list'])
        spk_list(self.extended_utts, paths['spk_list'])
        extract_transcript(self.extended_utts, paths['text'])


def list_wavs(corpus_dir):
    return glob.glob(path.join(corpus_dir, '**/*/*.wav'))


def list_wrds(corpus_dir):
    return glob.glob(path.join(corpus_dir, '**/*/*.wrd'))


def extract_wav(input_dir, output_dir):
    """
    Copy the audio file in the wavs folder, and return the list of audio files
    """
    fs = 16000  # sampling frequency of the input files in Hz
    nbits = 16  # each sample is coded on 16 bit in the input files
    
    if not(os.path.isdir(output_dir)):
        os.mkdir(output_dir)
    l = list_wavs(input_dir)
    res = []
    for wavfile in l:
        bname = path.basename(wavfile)
        outfile = os.path.join(output_dir, bname)
        res.append(outfile)
        #shutil.copy(wavfile, outfile)
    return res


def extract_utt(wrd_file):
    """Extract utterances in a .wrd file, splitting on interviewer or third person talking
    Format should be the new .wrd format, without header

    Returns a list of fragments: (start, end, ([word, ..], [phone, ..]))
    """
    words = []
    threshold = 0.5
    with open(wrd_file) as fin:
        for line in fin:
            aux = line.strip().split('\t')
            trans = aux[2].split('; ')
            words.append((float(aux[0]), float(aux[1]), trans[0], trans[2]))
    
    # finding split indexes:
    # IVER, long sil/noise
    #TODO: merge silences/noise before applying threshold
    trans = [word[2] for word in words]
    split = ([0]
             + [i for i, w in enumerate(words)
                if w[2][:5] == '<IVER' or (w[2][0] == '<' and w[1] - w[0] > threshold)]
             + [len(words)-1])

    # extend split to surrounding silence/noise
    for prev_index, index, next_index in zip(split[:-2], split[1:-1], split[2:]):
        i = index - 1
        while i > prev_index and words[i][2][0] == '<':
            split.append(i)
            i -= 1
        i = index + 1
        while i < next_index and words[i][2][0] == '<':
            split.append(i)
            i += 1

    
    # split and flatten 'words' by 'split'
    diff = lambda l1,l2: [x for x in l1 if x not in l2]
    keep = diff(range(len(words)), split)
    ranges = []
    frags = []
    for k, g in groupby(enumerate(keep), lambda (i,x):i-x):
        group = map(itemgetter(1), g)
        frags.append((words[group[0]][0], words[group[-1]][1],
                     [words[index][2] for index in group],
                     [words[index][3] for index in group]))

    return frags


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


def export_phones(utterances, output_file, silences=None, silence_file=None):
    """Extract the list of phones in the corpus
    """
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


# def strip_accolades(s):
# 	assert s[0] == "{" and s[-1] == "}", u"Bad formatting for word or transcript: {0}".format(s)
# 	return s[1:-1]


# def extract_dictionary(dictionary_file, output_file, words_to_drop=None):
# 	# read input file
# 	with codecs.open(dictionary_file, mode='r', encoding='UTF-8') as inp:
# 		lines = inp.readlines()
# 	# get rid of linebreaks
# 	# this does not take into account fancy unicode linebreaks
# 	# see: http://stackoverflow.com/questions/3219014/what-is-a-cross-platform-regex-for-removal-of-line-breaks
# 	lines = [re.sub(u"\r\n?|\n", u"", line) for line in lines]
# 	# parse input file
# 	words = []
# 	transcripts = []
# 	for line in lines:
# 		l = line.split(u" ")
# 		word = l[0]
# 		transcript = l[1:]
# 		# parse word
# 		word = strip_accolades(word)
# 		assert not u"{" in word
# 		# parse phonetic transcription
# 		t = u" ".join(transcript)
# 		t = strip_accolades(t)
# 		t = t.split(u" ")
# 		transcript = []
# 		for phone in t:
# 			assert phone, t  # check that transcription is not empty
# 			if phone[0] == u"{":
# 				p = phone[1:]
# 				assert p != u"WB", t
# 			elif phone[-1] == u"}":
# 				p = phone[:-1]
# 				assert p == u"WB", t
# 			else:
# 				p = phone
# 				assert p != u"WB", t
# 			assert not(u"{" in p), t
# 			if p != u"WB":
# 				transcript.append(p)
# 		transcript = u" ".join(transcript)
# 		words.append(word)
# 		transcripts.append(transcript)
# 	# generate output file
# 	with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
# 		for w, t in zip(words, transcripts):
# 			out.write(u"{0} {1}\n".format(w, t))


# # languages to be prepared
# languages = ['Mandarin', 'Vietnamese']
# # name of the folder in the raw distribution containing the transcriptions to be used
# transcript = {'Mandarin': 'rmn', 'Vietnamese': 'trl'}

# # path to a directory containing the raw ELRA distribution for the desired languages
# # it should contain folders named GlobalPhone-"name of language", for example
# # GlobalPhone-Mandarin or GlobalPhone-Vietnamese
# raw_path = "/Users/thomas/Documents/PhD/Recherche/Code/BuckeyeChallenge/GLOBALPHONE"
# # path to a directory containing the raw ELRA distribution for the phonetic dictionaries
# # for the desired languages
# # it should contain folders named GlobalPhoneDict-"name of language", for example
# # GlobalPhoneDict-Mandarin or GlobalPhoneDict-Vietnamese
# raw_dict_path = "/Users/thomas/Documents/PhD/Recherche/Code/BuckeyeChallenge/GLOBALPHONE"
# # path to a directory where the processed corpora is to be stored
# processed_path = "/Users/thomas/Documents/PhD/Recherche/databases/abkhazia/corpora"

# """
# # folder set up
# for lang in languages:
#         log_dir = os.path.join(processed_path, 'GP_{0}/logs'.format(lang))
#         if not(os.isdir(log_dir):
#                os.mkdir(log_dir)
#         data_dir = os.path.join(processed_path, 'GP{0}/data'.format(lang))
#         if not(os.isdir(data_dir)):
#                os.mkdir(data_dir)

# # log files config
# loggers = {}
# for lang in languages:
# 	loggers[lang] = logging.getLogger(lang)
# 	loggers[lang].setLevel(logging.DEBUG)
# 	log_file = os.path.join(processed_path, "GP_{0}/logs/data_preparation.log".format(lang))
# 	log_handler = logging.FileHandler(log_file, mode='w')
# 	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 	log_handler.setFormatter(formatter)
# 	log_handler.setLevel(logging.DEBUG)
# 	loggers[lang].addHandler(log_handler)



# ##########################
# ## I. Speech recordings ##
# ##########################

# for lang in languages:
# 	loggers[lang].info("Copying wav files")
# 	i = os.path.join(raw_path, "GlobalPhone-{0}/{0}/adc".format(lang))
# 	o = os.path.join(processed_path, "GP_{0}/data/wavs".format(lang))
# 	extract_wav(i, o)
# 	loggers[lang].info("Wav files copied")

# # Note: Ask database creator about clipping problems in Vietnamese?

# ############################
# ## II. List of utterances ##
# ############################

# for lang in languages:
# 	loggers[lang].info("Generating utterances list")
# 	wav_dir = os.path.join(processed_path, "GP_{0}/data/wavs".format(lang))
# 	utt_file = os.path.join(processed_path, "GP_{0}/data/segments".format(lang))
# 	utt_list(wav_dir, utt_file)
# 	loggers[lang].info("Utterances list generated")

# ###########################
# ## III. List of speakers ##
# ###########################
# # Note: more info on speakers is available in spk folders of the raw distributions

# for lang in languages:
# 	loggers[lang].info("Generating speakers list")
# 	wav_dir = os.path.join(processed_path, "GP_{0}/data/wavs".format(lang))
# 	spk_file = os.path.join(processed_path, "GP_{0}/data/utt2spk".format(lang))
# 	spk_list(wav_dir, spk_file)
# 	loggers[lang].info("Speaker list generated")

# #######################
# ## IV. Transcription ##
# #######################	

# for lang in languages:
# 	loggers[lang].info("Generating utterances transcriptions")
# 	transcript_dir = os.path.join(raw_path, "GlobalPhone-{0}/{0}/{1}".format(lang, transcript[lang]))
# 	text_file = os.path.join(processed_path, "GP_{0}/data/text".format(lang))
# 	extract_transcript(transcript_dir, text_file)
# 	loggers[lang].info("Utterances transcription generated")

# ########################
# ## V. Phone inventory ##
# ########################

# for lang in languages:
# 	loggers[lang].info("Creating phone inventory")
# 	phoneset = importlib.import_module('phoneset_{0}'.format(lang))
# 	output_folder = os.path.join(processed_path, "GP_{0}/data".format(lang))
# 	export_phones(phoneset.phones, output_folder, phoneset.silences, phoneset.variants)
# 	loggers[lang].info("Phone inventory created")

# #############################
# ## VI. Phonetic dictionary ##
# #############################

# for lang in languages:
# 	loggers[lang].info("Generating phonetic dictionary")
# 	dictionary_file = os.path.join(raw_dict_path, "GlobalPhoneDict-{0}/{0}-GPDICT.txt".format(lang))
# 	output_file = os.path.join(processed_path, "GP_{0}/data/lexicon.txt".format(lang))
# 	# some dictionaries are distributed with formating errors or unused words
# 	# we use a language-specific script to correct them
# 	# the result is put in a temporary file
# 	dict_module = importlib.import_module('dictionary_{0}'.format(lang))
# 	corrected_dict_file = dict_module.correct_dictionary(dictionary_file)
# 	# then we use a generic script to put dictionaries in abkhazia format
# 	extract_dictionary(corrected_dict_file, output_file)
# 	# remove temporary dict file
# 	os.remove(corrected_dict_file)
# 	loggers[lang].info("Phonetic dictionary generated")
# # Note: evaluate potential benefits of using the ignored secondary pronunciation in Vietnamese?
# """
