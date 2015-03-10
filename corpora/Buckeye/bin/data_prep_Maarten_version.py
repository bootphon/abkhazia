# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 15:12:26 2015

@author: Maarten Versteegh, Roland Thiollière, Thomas Schatz
"""
"""
Buckeye ...
-> get Maarten scripts
-> Decide on what datasets to prepare and merge with Roland
Format of two things from Maarten + what Xuan-Nga put on Oberon
"""

from collections import namedtuple
from collections import Counter
import os
import textgrid
import fnmatch
import logging
import codecs
import re
import shutil


SpeechChunk = namedtuple('SpeechChunk', ['file', 'start', 'stop', 'transcript'])

# filter out .DS_Store files from MacOS if any
def list_dir(d):
	return [e for e in os.listdir(d) if e != '.DS_Store']


########################################################
###################### Raw corpus ######################
########################################################

# log file contains indication about parts where there is overlap
# between interviewer and interviewee speech or modality of voice
# (creaky, modal...), but the corresponding events don't have a 
# big effect on the signal and we just ignore them


# there are 121, 122 labels in the second column of phone
# and word files whose meaning I don't understand
def read_raw_phn(fname):
	bname = os.path.basename(fname)
	phones = []
	body = False  # flag used to ignore the file header
	start = "0."
	for line in open(fname):
		if body:
			try:
				line = line.strip()
				# some phones are marked with a * for some reason I don't
				# know, we just ignore them
				if not line:
					print('RAW PHN: empty line!')
				else:
					if line[-1] == '*':
						line = line.split(';')[0].strip()				
					# second part of the following parse is just a blank space
					# third part seems to be either 121 or 122 with
					# meaning unknown
					stop, _, _, phone = line.split(' ')
					phones.append(SpeechChunk(bname, start, stop, phone))
					start = stop
			except ValueError:
				print('RAW PHN: ' + line.strip())
		else:
			if line.strip() == '#':
				body = True
	return phones


def read_raw_wrd(fname):
	bname = os.path.basename(fname)
	words = []
	standard_pronunciations = []
	reported_pronunciations = []
	body = False  # flag used to ignore the file header
	start = "0."
	for line in open(fname):
		if body:
			splitline = line.strip().split(' ')
			stop = splitline[0]
			try:
				wordchunk = ' '.join(splitline[2:])
				word, std_pron, rep_pron, POS = wordchunk.split(';')
				word = word.strip()
				std_pron = std_pron.strip()
				rep_pron = rep_pron.strip()
				words.append(SpeechChunk(bname, start, stop, word))
				standard_pronunciations.append(std_pron)
				reported_pronunciations.append(rep_pron)
			except ValueError:
				print('RAW WRD: '+ line.strip())
			start = stop
		else:
			if line.strip() == '#':
				body = True
	return words, standard_pronunciations, reported_pronunciations


def rglob(rootdir, pattern):
	for root, _, files in os.walk(rootdir):
		for basename in files:
			if fnmatch.fnmatch(basename, pattern):
				yield os.path.join(root, basename)


def read_raw(buckeye_folder):
	phones = [chunk for f in rglob(buckeye_folder, 's*.phones') for chunk in read_raw_phn(f)]
	words = [(chunk, std_pron, rep_pron) for f in rglob(buckeye_folder, 's*.words') for chunk, std_pron, rep_pron in zip(*read_raw_wrd(f))]
	wavs = [os.path.basename(f) for f in rglob(buckeye_folder, 's*.wav')]
	return wavs, phones, words


########################################################
###################### LSCP corpus #####################
########################################################
def parse_textgrid(filename):   
	"""
	the whole transcript is returned as a list of 
	triplets with format: (onset, offset, transcript)
	"""
	tg = textgrid.TextGrid.load(filename)  # no context management ?
	assert len(tg.tiers) == 1
	transcript = tg.tiers[0].simple_transcript
	return transcript


def read_lscp_phn(filename):
	bname = os.path.basename(filename)
	transcript = parse_textgrid(filename)
	phones = []
	for on, off, phone in transcript:
		phones.append(SpeechChunk(bname, on, off, phone))
	return phones


def read_lscp_wrd(filename):
	bname = os.path.basename(filename)
	transcript = parse_textgrid(filename)
	words = []
	standard_pronunciations = []
	reported_pronunciations = []
	for on, off, word_line in transcript:
		try:
			if '<' in word_line:
				pass
			else:
				word, std_pron, rep_pron, POS = word_line.split(';')
				word = word.strip()
				words.append(SpeechChunk(bname, on, off, word))
				std_pron = std_pron.strip()
				rep_pron = rep_pron.strip()
				standard_pronunciations.append(std_pron)
				reported_pronunciations.append(rep_pron)
		except ValueError:
			print('LSCP WRD: ' + word_line.strip())
	return words, standard_pronunciations, reported_pronunciations


def read_lscp(lscp_path):
	wav = os.path.join(lscp_path, 'wav')
	phn = os.path.join(lscp_path, 'phn_TextGrid')
	wrd = os.path.join(lscp_path, 'wrd_TextGrid')
	phones = [chunk for f in list_dir(phn) for chunk in read_lscp_phn(os.path.join(phn, f))]
	words = [(chunk, std_pron, rep_pron) for f in list_dir(wrd) for chunk, std_pron, rep_pron in zip(*read_lscp_wrd(os.path.join(wrd, f)))]
	wavs = list_dir(wav)  # use the raw waves, because we don't want the cut into utterances
	return wavs, phones, words


########################################################
##################### Maarten corpus ###################
########################################################
def read_maarten_phn_or_wrd(filename, offsets):
	bname = os.path.basename(filename)
	# find utterance offset
	utt = os.path.splitext(bname)[0]
	offset = offsets[utt]
	# read all chunks
	chunks = []
	for line in open(filename):
		on, off, transcript = line.strip().split(' ')
		chunks.append(SpeechChunk(utt, float(on)+float(offset), float(off)+float(offset), transcript))
	return chunks


def read_utterances_offsets(filename):
	offsets = {}
	for line in open(filename):
		big_f, on, off, utt = line.strip().split(' ')
		offsets[utt] = on
	return offsets

	
def read_maarten(maarten_path):
	# get offset for each utterance	
	utt_positions = os.path.join(maarten_path, 'ENGLISH_SPLIT_LOG')
	offsets = read_utterances_offsets(utt_positions)
	# read transcript for each utterance
	#wav = os.path.join(maarten_path, 'wav')
	phn = os.path.join(maarten_path, 'phn')
	wrd = os.path.join(maarten_path, 'wrd')
	phones = [chunk for f in list_dir(phn) for chunk in read_maarten_phn_or_wrd(os.path.join(phn, f), offsets)]
	words = [chunk for f in list_dir(wrd) for chunk in read_maarten_phn_or_wrd(os.path.join(wrd, f), offsets)]
	#wavs = list_dir(wav)
	return phones, words


########################################################
###################### Main script #####################
########################################################


root = '/Users/thomas/Documents/PhD/Recherche/'
raw_path = os.path.join(root, 'databases', 'BUCKEYE')
lscp_path = os.path.join(root, 'Code', 'BuckeyeChallenge', 'buckeye', 'Buckeye')
maarten_path = os.path.join(root, 'Code', 'BuckeyeChallenge', 'buckeye', 'buckeye_modified')
output_path = os.path.join(root, 'other_gits', 'abkhazia', 'corpora', 'Buckeye')

# folder set up
if not(os.path.isdir(output_path)):
	os.makedirs(output_path)
log_dir = os.path.join(output_path, 'logs')
if not(os.path.isdir(log_dir)):
	os.makedirs(log_dir)
data_dir = os.path.join(output_path, 'data')
if not(os.path.isdir(data_dir)):
	os.makedirs(data_dir)

# log files config
log = logging.getLogger()
log.setLevel(logging.DEBUG)
log_file = os.path.join(output_path, "logs/data_preparation.log")
print("Log file in {0}".format(log_file))
log_handler = logging.FileHandler(log_file, mode='w')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
log_handler.setLevel(logging.DEBUG)
log.addHandler(log_handler)


# read the three versions of the corpus
wavs_raw, phones_raw, words_raw = read_raw(raw_path)
print('Starting lscp')
wavs_mod, phones_mod, words_mod = read_lscp(lscp_path)
print('Starting Maarten')
phones_maa, words_maa = read_maarten(maarten_path)
# get rid of file s0103a (which has many problems, that we are 
# not planning to correct apparently)
# also wavefile s1901b seem to have been cut short
# all utterances from Maarten for this file starting from 252 have to be thrown out
def accept(id):
	wav, utt = id.split('_')
	answer = wav != 's0103a'
	answer = answer and not(wav == 's1901b' and int(utt) >= 252)
	return answer

phones_maa = [phone for phone in phones_maa if accept(phone.file)]
words_maa = [word for word in words_maa if accept(word.file)]



############################
# Pronunciation dictionary #
############################
# First create a pronunciation dictionary 
# for Maarten's version as complete as possible
# from the standard pronunciations available for the raw
# and modified corpora

lexicon_maa = Counter([e.transcript for e in words_maa])
lexicon_raw = Counter([e.transcript for e, f, g in words_raw])
lexicon_mod = Counter([e.transcript for e, f, g in words_mod])

def get_standard_prons(words):
	prons = {}	
	for chunk, std_pron, _ in words:
		word = chunk.transcript
		if not(word in prons):
			prons[word] = set()
		prons[word].add(std_pron)
	return prons

raw_prons = get_standard_prons(words_raw)
mod_prons = get_standard_prons(words_mod)
	
# a few words have more than one pronunciation
# in the raw or mod corpus
# for those words, we follow the CMUdict transcription

# it might be useful to compare other words with CMUdict
# too to see if the proposed transcriptions match, but
# I'm not sure which source is supposed to be more authoritative
# for Buckeye (Ohio speakers)
# Note that the Buckeye original dictionary uses more phones
# than the CMU (e.g. dx or em)
raw_prons['o'] = set(['ow'])
mod_prons['o'] = set(['ow'])
raw_prons['research'] = set(['r iy s er ch'])	
mod_prons['research'] = set(['r iy s er ch'])
raw_prons['uh'] = set(['ah'])
mod_prons['uh'] = set(['ah'])
raw_prons['ah'] = set(['aa'])
mod_prons['ah'] = set(['aa'])
raw_prons['almost'] = set(['ao l m ow s t'])
mod_prons['almost'] = set(['ao l m ow s t'])
raw_prons['sports'] = set(['s p ao r t s'])
mod_prons['sports'] = set(['s p ao r t s'])
# this one is not in the cmu... I chose the full form
# instead of just 'n ow'
raw_prons['yknow'] = set(['y uw n ow'])
mod_prons['yknow'] = set(['y uw n ow'])

# now check that all words in Maarten's version have 0 or 
# 1 pronunciation and get list of words with 0 pronunciation
missing_prons = []
for word in lexicon_maa:
	if word in raw_prons and len(raw_prons[word]) > 1:
		raise ValueError, word
	if word in mod_prons and len(mod_prons[word]) > 1:
		raise ValueError, word
	if word in mod_prons and word in raw_prons:
		if mod_prons[word] != raw_prons[word]:
			raise ValueError, word
	if not(word in mod_prons) and not(word in raw_prons):
		missing_prons.append(word)
files = [word.file for word in words_maa if word.transcript in missing_prons]
nb_missing_utts = len(set(files))
nb_utts = len(set([word.file for word in words_maa]))

log.debug("{0} word types have unknown pronunciation".format(len(missing_prons)))
log.debug("These word types are present in {0} out of {1} utterances".format(nb_missing_utts, nb_utts))

# check format of pronunciation strings and word strings
# and get phone inventory
prons = {}
phones = []
for word in lexicon_maa:
	if word in raw_prons:
		pron = raw_prons[word].pop()
	elif word in mod_prons:
		pron = mod_prons[word].pop()
	else:
		continue
	assert re.match('[a-z]+$', word), word
	wrd_phones = pron.split(' ')
	for phone in wrd_phones:
		assert re.match('[a-z]+$', phone), phone
		phones.append(phone)
	prons[word] = ' '.join(wrd_phones)

phones_in_lex = Counter(phones)

prons_splitted = {}
for word in prons:
	prons_splitted[word] = prons[word].split(' ')
phones_in_text = [phone for chunk in words_maa if (chunk.transcript in prons) for phone in prons_splitted[chunk.transcript]]
phones_in_text = Counter(phones_in_text)

# certain phones occur very rarely
# get rid of those by adapting the pronunciations
# of the words in which they appear
# also get rid of some typos at the same time
# As a criterion we get rid of any phone with either less
# than 200 occurences or less than
# 20 different word types
# The removed phones are: 
#	tq, nx, ao, em and h which is a typo
# for some reason 'eng' is not present at all 
# in the standard pronunciations
# The only remaining allophonic phones are dx, el and en
# They could be removed too, but it would require adapting
# a much larger number of pronunciations (or maybe
# this could be done by using the CMUdict as a reference)
# Also 'ao' which is not supposed to be allophonic is present
# only in 4 words (126 total occurences) and gets thrown away

# getting rid of tq (+one dx) -> t (and d)
prons['dont'] = 'd ow n t'
# getting rid of nx -> n
prons['heroin'] = 'hh eh r ow ih n'
prons['chanukah'] = 'hh aa n ah k ah'
# getting rid of h (which is not supposed to be in
# inventory to begin with ????) -> hh
prons['whitehall'] = 'w ay t hh aa l'
prons['mahal'] = 'm ah hh aa l'
prons['whitehouse'] = 'w ay t hh aw s'
prons['hoosier'] = 'hh uw z y er'
# getting rid of ao, arbitrarily replaced by aa
# maybe a phonologist should check that
prons['alzheimers'] = 'aa l s ay m er z'
prons['chorus'] = 'k aa r ah s'
prons['sports'] = 's p aa r t s'
prons['almost'] = 'aa l m ow s t'
# getting rid of em -> m
prons['mhm'] = 'm hh m'
prons['hm'] = 'hh m'
prons['mm'] = 'm'
prons['hmm'] = 'hh m'
# getting rid of dx -> t or d
prons['introvertal'] = 'ih n t r ow v er t ah l'
prons['disparity'] = 'd ih s p eh r ah t iy'
prons['yadda'] = 'y aa d ah'
prons['yadda'] = 'y aa d ah'
prons['skateboarding'] = 's k ey t b ow r d ih ng'
prons['shoulda'] = 'sh uh d ah'
prons['doody'] = 'd uw d iy'
prons['tattletale'] = 't ae t el t ey l'
prons['lotta'] = 'l aa t ah'
prons['ritalin'] = 'r ih t ah l ah n'
prons['rowed'] = 'r ow d'
prons['littlest'] = 'l ih t el ah s t'
prons['exporting'] = 'eh k s p ow r t ah ng'


prons_splitted = {}
for word in prons:
	prons_splitted[word] = prons[word].split(' ')
phones_in_text = [phone for chunk in words_maa if (chunk.transcript in prons) for phone in prons_splitted[chunk.transcript]]
phones_in_text = Counter(phones_in_text)
assert(len(phones_in_text) == 40)


def write_dict(pronunciations, output_file):
	with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
		for word in pronunciations:
			out.write(u"{0} {1}\n".format(word, pronunciations[word]))

write_dict(prons, os.path.join(data_dir, 'lexicon.txt'))
		
############################
# 	 Phone inventory	 #
############################
def write_phone(phones, output_file):
	with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
		for phone in phones:
			out.write(u"{0} {1}\n".format(phone, phones[phone]))

# ad hoc, here we have just what we need in phones_in_text
# but it could happen that there are more phones in the dict than in the text
phoneset = set(phones_in_text.keys())
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
	('tq', u'ʔ')
]
phones = {}
for phone in phoneset:
	for p, ipa in Buckeye_phones:
		if p == phone:
			phones[phone] = ipa

write_phone(phones, os.path.join(data_dir, 'phones.txt'))


###############################
# text, segments and speakers #
###############################
def extract_data(words, text_file, utt2spk_file, segments_file, wav_dir_in, wav_dir_out):	
	# the order in words is important for this part
	# where we group words by utterance in time order
	utts = {}
	utt2spk = {}
	current_utt = []
	utt_id = None
	for chunk in words:
		if chunk.file != utt_id:
			if not(utt_id is None):
				utts[utt_id] = current_utt
				utt2spk[utt_id] = utt_id[:3]
			utt_id = chunk.file
			file_id, _ = chunk.file.split('_')
			current_utt = SpeechChunk(file_id, chunk.start, chunk.stop, chunk.transcript)
		else:
			current_utt = SpeechChunk(
								current_utt.file,
								current_utt.start,
								chunk.stop, 
								current_utt.transcript + ' ' + chunk.transcript
								)
	with codecs.open(text_file, mode='w', encoding='UTF-8') as out:
		for utt in utts:			
			out.write("{0} {1}\n".format(utt, utts[utt].transcript))
	with codecs.open(utt2spk_file, mode='w', encoding='UTF-8') as out:
		for utt in utts:			
			out.write("{0} {1}\n".format(utt, utt2spk[utt]))
	with codecs.open(segments_file, mode='w', encoding='UTF-8') as out:
		for utt in utts:			
			out.write("{0} {1} {2:.3f} {3:.3f}\n".format(utt, utts[utt].file + '.wav', utts[utt].start, utts[utt].stop))
	wavs = set([utts[utt].file for utt in utts])
	if not(os.path.isdir(wav_dir_out)):
		os.makedirs(wav_dir_out)
	for wav in wavs:
		wavefile = wav + '.wav'
		src = os.path.join(wav_dir_in, wavefile)
		dst = os.path.join(wav_dir_out, wavefile)
		shutil.copy(src, dst)
		
extract_data(
		words_maa,
		os.path.join(data_dir, 'text.txt'), 
		os.path.join(data_dir, 'utt2spk.txt'),
		os.path.join(data_dir, 'segments.txt'),
		os.path.join(lscp_path, 'wav'),
		os.path.join(data_dir, 'wavs')
		)
	
"""
ISSUES
 
file s0103a.wav is missing altogether in the lscp-modified corpus, is this normal?
-> it's normal since this file has many issues (will it eventually be corrected?)
-> it actually needs to be removed from the evaluation

I have no idea on what version of the corpus Maarten worked, all that I could get
is the output, already segmented into utterances + the log containing the position
of the utterances into the big wavefiles

In Maarten's corpus:
	283 word types without a standard pronunciation in raw or mod
	8260/51 110 utterances concerned
	some types look like typos or tentatives to render weird pronunciations
	in writing, other should be found in CMU dictionary
	For now: we just treat them as OOV items

Many issues with raw files format, and many of them also with modified 
(and probably simply dropped from Maarten version)

Also wavefile s1901b seem to have been cut short
all utterances from Maarten for this file starting from 252 have to be thrown out


Allophonic phones
	Possible mapping:
		el -> l
		em -> m
		en -> n
		eng -> ng
		tq, dx, nx -> sil/pau or keep dx, nx as a flap? or nx->n?

TONIGHT
1 - Maarten + lexical -> abkhazia 
2 - abkhazia -> kaldi
--- from here keep small dev set on mac and move to oberon
3 - select kaldi parameters (LM (n in n-grams) + SI and SA * 2)
using whole corpus excepted a small validation set
4 - retrain on whole with those params
5 - get forced alignment of Maarten's subset from this model
6 - use this to recompile a different task file for the challenge and get MFCC
baseline on it and compare with previous analyses to see if better stability
with new alignments
_____________________________
TOMORROW
7 - redo training and param selection on whole-(challenges sets) with a validation
set for the params also outside challenge sets
8 - use obtained model to get gaussian posteriors, weird posteriors
and best translation for the challenge sets
9 - get ABX scores on these various representations using various metrics
on the original challenge, check stability etc. and this should give the final
baselines for the Buckeye part of the challenge

10 - Same thing on Xitsonga...


get standard transcription from raw corpus, check for homophones and multiple different
transcriptions

compare with CMU? (maybe not if standard phoneset matches CMU?)

Generate kaldi files based on Maarten
"""



# raw Buckeye
# LSCP Buckeye (provisoire) -> textgrids
# Maarten produced buckeye from raw

# 1. compare raw, LSCP and Maarten outputs content: nb_words token and type, nb_phones token and types

# 2. get utterances from list already there?
# compare with Roland and Maarten's criterions

# 3. filter out some stuff (iver and pure noise?)
# 4. separate clean and less clean parts
# 5. need to be able to train on a set different from Maarten's subset (just use different talkers for simplicity?)
