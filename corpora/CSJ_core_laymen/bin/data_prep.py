# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 01:52:19 2015

@author: Thomas Schatz
"""
import os
import shutil
import codecs
from collections import namedtuple
from abkhazia.utilities.basic_io import cpp_sort

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

"""
MoraId == number or x or φ ??
TagUncertainEnd=1
TagUncertainStart=1
<Noise
<NonLinguisticSound
LUWDictionaryForm=xxx(+)

Alignment of various levels (sentences and phones)
For 8 files: bad portions ???

# get info about speakers (M/F) into utt2spk and change name of files for more consistency
# what about non-core files?

- keep FV and VN separate ? (fricative and voicing ?)
- some empty sentences because they contain NonLinguisticSound instead of SUW balise, treat these differently ?
- isolated H sentences ?? maybe because some long vowel are spread across two SUW for some reason ?
need to listen to it. If it is the case, in preprocessing regroup these SUW.

TODO remove redundancy from utt_ids (spk_id present twice ...)
"""

Phone = namedtuple('Phone', 'id type start end')
Phoneme = namedtuple('Phone', 'id phones start end')
Word = namedtuple('Word', 'phonemes start end')
Utt = namedtuple('Utt', 'words start end channel')


def parse_CSJ_core_xml(xml_file):
	"""
	Parse raw transcript
	"""
	tree = ET.ElementTree(file=xml_file)
	talk = tree.getroot()
	talk_id = talk.attrib["TalkID"]	
	speaker = talk.attrib["SpeakerID"]
	# make sure all speaker-ids have same length
	if len(speaker) < 4:
		speaker = "0"*(4-len(speaker)) + speaker
	else:
		assert len(speaker) == 4, talk_id
	gender = 'M' if talk.attrib["SpeakerSex"] == u"男" else 'F'  # using kanji for 'male'
	spk_id = gender + speaker

	if talk_id[0] == "D":
		is_dialog = True
	else:
		is_dialog = False
	# Utterance level
	utts = {}
	for ipu in talk.iter("IPU"):
		utt_id = spk_id + u"_" + talk_id + u"_" + ipu.attrib["IPUID"]
		if is_dialog:
			channel = ipu.attrib["Channel"]
		else:
			channel = None
		utt_start = float(ipu.attrib["IPUStartTime"])
		utt_stop = float(ipu.attrib["IPUEndTime"])
		# Word level - Short Words Units (SUW) are taken as 'words'
		words = []
		for suw in ipu.iter("SUW"):
			# Phoneme level
			phonemes = []
			for phoneme in suw.iter("Phoneme"):
				phoneme_id = phoneme.attrib["PhonemeEntity"]
				# Phone level (detailed phonetic)
				phones = []
				for phone in phoneme.iter("Phone"):
					start = float(phone.attrib["PhoneStartTime"])
					stop = float(phone.attrib["PhoneEndTime"])
					id = phone.attrib["PhoneEntity"]
					phn_class = phone.attrib["PhoneClass"]
					phones.append(Phone(id, phn_class, start, stop))
				if phones:
					phonemes.append(Phoneme(phoneme_id, phones, phones[0].start, phones[-1].end))
				else:
					print(utt_id)
			if phonemes:
				words.append(Word(phonemes, phonemes[0].start, phonemes[-1].end))
			else:
				try:
					moras = [mora.attrib["MoraEntity"] for mora in suw.iter("Mora")]
					print(moras)
				except:
					pass
				print(utt_id)
				#FIXME understand this 
				#assert u"φ" in moras, utt_id
		utts[utt_id] = Utt(words, utt_start, utt_stop, channel)
	return utts


def check_transcript_consistency(utts):
	pass
	# TODO: check consistency of starts, stops, subsequent starts at all levels
	# and the across level consistency


def extract_basic_transcript(utts, encoding=None):
	lexicon = {}
	new_utts = {}
	for utt_id in utts:
		utt = utts[utt_id]
		if not(utt.words):
			print 'Empty utt: ' + utt_id
		else:
			#TODO log these (and correct these before this step)
			if utt.words[0].start < utt.start:
				print utt_id + ' start: ' + str(utt.start) + ' - ' + str(utt.words[0].start)
			if utt.words[-1].end  > utt.end:
				print utt_id + ' end: ' + str(utt.end) + ' - ' + str(utt.words[-1].end)
			start = min(utt.words[0].start, utt.start)
			stop = max(utt.words[-1].end, utt.end)
			words = []
			for word in utt.words:
				# use phonemic level
				phonemes = reencode([phoneme.id for phoneme in word.phonemes], encoding)
				#print('-'.join(phonemes))
				#print('-'.join([phoneme.id for phoneme in word.phonemes]))
				if phonemes == ['H']:  # just drop these for now
					pass # log this
				else:
					word = u"-".join(phonemes)
					if not(word in lexicon):
						lexicon[word] = phonemes
					words.append(word)
			new_utts[utt_id] = {'words': words, 'start': start, 'end': stop}
	return new_utts, lexicon


def reencode(phonemes, encoding=None):
	vowels = ['a', 'e', 'i', 'o', 'u']
	stops = ['t', 'ty', 'b', 'by', 'g', 'gj', 'gy', 'k', 'ky', 'kj', 'p', 'py', 'd', 'dy']
	affricates = ['z', 'zy', 'zj', 'c', 'cy', 'cj']
	fricatives = ['s', 'sj', 'sy', 'z', 'zy', 'zj', 'h', 'F', 'hy', 'hj']
	obstruents = affricates + fricatives  + stops

	phonemes_1 = []
	for phoneme in phonemes:
		# 1 - Noise and rare phonemes
		out_phn = phoneme
		# getting rid of very rare phones as vocal noise
		if out_phn in ['kw', 'v', 'Fy']:
			out_phn = 'VN'
		# rewriting FV and VN (fricative voicing and vocal noise) as SPN (spoken noise)
		if out_phn in ['FV', 'VN']:
			out_phn = 'SPN'
		# rewriting ? as NSN (generic noise)
		if out_phn == '?':
			out_phn = 'NSN'
		# 2 - breaking clusters
		seg_1 = {
			'ky': 'k', 
			'ty': 't',
			'ry': 'r',
			'cy': 't',
			'cj': 't',
			'c': 't',
			'py': 'p',
			'ny': 'n',
			'by': 'b',
			'my': 'm',
			'hy': 'h',
			'gy': 'g',
			'dy': 'd'
			}
		seg_2 = {
			'ky': 'y', 
			'ty': 'y',
			'ry': 'y',
			'cy': 'sy',
			'cj': 'sj',
			'c': 's',
			'py': 'y',
			'ny': 'y',
			'by': 'y',
			'my': 'y',
			'hy': 'y',
			'gy': 'y',
			'dy': 'y'
			}
		if out_phn in seg_1:
			out_phns = [seg_1[out_phn], seg_2[out_phn]]
		else:
			out_phns = [out_phn]
		# 3 - group allophonic variants according to phonetics
		mapping = {
			'zj': 'zy',
			'cj': 'cy',
			'sj': 'sy',
			'nj': 'n',
			'kj': 'k',
			'hj': 'h',
			'gj': 'g'
			}
		out_phns = [mapping[phn] if phn in mapping else phn for phn in out_phns]
		phonemes_1 = phonemes_1 + out_phns
	# 4 - Q before obstruent as geminate (long obstruent)
	if len(phonemes_1) <= 1:
		phonemes_2 = phonemes_1
	else:
		phonemes_2 = []
		previous = phonemes_1[0]
		for phoneme in phonemes_1[1:]:
			out_phn = phoneme
			if previous == 'Q':
				assert not(out_phn == 'Q'), "Two successive 'Q' in phoneme sequence"
				if out_phn in obstruents:
					previous = out_phn + ':'
				else:
					phonemes_2.append('Q')  # Q considered a glottal stop in other contexts
					previous = out_phn
			else:
				phonemes_2.append(previous)
				previous = out_phn
		phonemes_2.append(previous)  # don't forget last item
	# 5 - H after vowel as long vowel
	if len(phonemes_2) <= 1:
		if 'H' in phonemes_2:
			print "Isolated H: " + str(phonemes) + str(phonemes_1)
		phonemes_3 = phonemes_2
	else:
		phonemes_3 = []
		previous = phonemes_2[0]
		assert not(previous == 'H'), "Word starts with H"
		for phoneme in phonemes_2[1:]:
			out_phn = phoneme
			if out_phn == 'H':
				assert not(previous == 'H'), "Two successive 'H' in phoneme sequence"
				if previous in vowels:
					phonemes_3.append(previous + ':')
				else:
					assert(previous == 'N'), "H found after neither N nor vowel"
					phonemes_3.append(previous)  # drop H after N
				previous = 'H'
			else:
				if previous != 'H':
					phonemes_3.append(previous)
				previous = out_phn
		if previous != 'H':
			phonemes_3.append(previous)  # don't forget last item
	return phonemes_3



	# group allophonic variants according to phonetics, is there really non-allophonic ones? Not if we consider 'y' as a phone
	# Q -> long obstruents
	# other q's -> glottal stops ?
	# NH -> N
	# other H -> long vowels





"""
Export to abkhazia format
"""


#output_folder = "/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/corpora/CSJ_core_laymen/data/"
#data_files = ["S07M0833"]
#xml_dir = "/Users/thomas/Documents/PhD/Recherche/databases/CSJ"
#wav_dir = "/Users/thomas/Documents/PhD/Recherche/databases/CSJ"


#TODO get this path relative to the script
output_folder = "/fhgfs/bootphon/scratch/thomas/abkhazia/corpora/CSJ_core_laymen/data/"
data_files = os.listdir("/fhgfs/bootphon/data/raw_data/CSJ/XML")
# select laymen talks only + remove extension + only from CORE part of the corpus
script_dir = os.path.dirname(os.path.realpath(__file__))
core_files = os.path.join(script_dir, 'CSJ_core.txt')
with open(core_files, 'r') as fh:
	core_files = [l[:-1] for l in fh.readlines()] # remove new lines
print(core_files)
data_files = [f.replace('.xml', '') for f in data_files]
data_files = [f for f in data_files if f[0] == 'S' and f in core_files]
print(len(data_files))

xml_dir = "/fhgfs/bootphon/data/raw_data/CSJ/XML"
wav_dir = "/fhgfs/bootphon/data/raw_data/CSJ/Waveforms"


# gather label data
all_utts = {}
lexicon = {}
for data_file in data_files:
	xml_file = os.path.join(xml_dir, data_file + '.xml')
	utts = parse_CSJ_core_xml(xml_file)
	utts, utt_lexicon = extract_basic_transcript(utts)
	for utt_id in utts:
		assert not(utt_id in all_utts), utt_id
		all_utts[utt_id] = utts[utt_id]
	for word in utt_lexicon:
		if not(word in lexicon):
			lexicon[word] = utt_lexicon[word]


# wav folder
output_dir = os.path.join(output_folder, 'wavs')
# create or clean output_dir
if os.path.isdir(output_dir):
	files = os.listdir(output_dir)
	for f in files:
		os.remove(os.path.join(output_dir, f))
else:
	os.mkdir(output_dir)
for f in data_files:
	source = os.path.join(wav_dir, f + '.wav')
	target = os.path.join(output_dir, f + '.wav')
	shutil.copy(source, target)

# utt2spk
output_file = os.path.join(output_folder, 'utt2spk.txt')
with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
	for utt_id in all_utts:
		spk_id = utt_id.split("_")[0]
		out.write(u"{0} {1}\n".format(utt_id, spk_id))
cpp_sort(output_file)

# segments
output_file = os.path.join(output_folder, 'segments.txt')	
with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
	for utt_id in all_utts:
		wavefile = utt_id.split("_")[1] + ".wav"
		start = all_utts[utt_id]['start']
		stop = all_utts[utt_id]['end']
		out.write(u"{0} {1} {2} {3}\n".format(utt_id, wavefile, start, stop))
cpp_sort(output_file)

# text
output_file = os.path.join(output_folder, 'text.txt')
with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
	for utt_id in all_utts:
		words = u" ".join(all_utts[utt_id]['words'])
		out.write(u"{0} {1}\n".format(utt_id, words))
cpp_sort(output_file)

# dictionary
# ad hoc ...
output_file = os.path.join(output_folder, 'lexicon.txt')
with codecs.open(output_file, mode='w', encoding='UTF-8') as out:
	for word in lexicon:
		transcript = u" ".join(lexicon[word])
		out.write(u"{0} {1}\n".format(word, transcript))
cpp_sort(output_file)

# phones
all_phones = set([phone for transcript in lexicon.values() for phone in transcript])

# Sources:
# https://en.wikipedia.org/wiki/Japanese_phonology
# book: the Sounds of Japanese
#TODO the IPA transcription needs to be more carefully chosen
vowels = [
	('a', u'ä'),
	('e', u'e'),
	('i', u'i'),
	('o', u'o'),
	('u', u'ɯ'),  # this one has lip-compression...
	('a:', u'ä:'),
	('e:', u'e:'),
	('i:', u'i:'),
	('o:', u'o:'),
	('u:', u'ɯ:')
]

# geminates: look at the effectives
consonants = [
	('F', u'ɸ'),  # not sure about this one
	('F:', u'ɸ:'),  # not sure about this one
	('N', u'ɴ'),
	('Q', u'ʔ'),
	('b', u'b'),
	('b:', u'b:'),  # is this really a geminate (with a voiced stop ?)
	('d', u'd'),
	('d:', u'd:'),  # is this really a geminate (with a voiced stop ?)
	('g', u'g'),
	('g:', u'g:'),  # is this really a geminate (with a voiced stop ?)
	('h', u'h'),
	('k', u'k'),
	('k:', u'k:'),
	('m', u'm'),
	('n', u'n'),
	('p', u'p'),
	('p:', u'p:'),
	('r', u'r'),
	('s', u's'),
	('s:', u's:'),
	('sy', u'ɕ'),
	('sy:', u'ɕ:'),
	('t', u't'),
	('t:', u't:'),
	('w', u'w'),  # lip-compression here too...
	('y', u'j'),
	('z', u'z'),
	('zy', u'ʑ')  # very commonly an affricate...
	('zy:', u'ʑ:')
]

phones = {}
for s, ipa in consonants:
	assert not(s in phones)
	phones[s] = ipa
for s, ipa in vowels:
	assert not(s in phones)
	phones[s] = ipa

silences = ['SPN', 'NSN']
variants = []

# piece of code from GP_Mandarin
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


