
import codecs
import os.path as p
import random
import subprocess
import os
import shutil
import numpy as np


#TODO share this with validate_corpus.py
def basic_parse(line, filename):
	# check line break
	assert not('\r' in line), "'{0}' contains non Unix-style linebreaks".format(filename)
	# check spacing
	assert not('  ' in line), "'{0}' contains lines with two consecutive spaces".format(filename)
	# remove line break
	line = line[:-1]
	# parse line
	l = line.split(" ")
	return l


def cpp_sort(filename):
	# there is redundancy here but I didn't check which export can be 
	# safely removed, so better safe than sorry
	os.environ["LC_ALL"] = "C"
	subprocess.call("export LC_ALL=C; sort {0} -o {1}".format(filename, filename), shell=True, env=os.environ)


def read_utt2spk(filename):
	utt_ids, speakers = [], []
	with codecs.open(filename, mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	for line in lines:
		l = basic_parse(line, filename)
		assert(len(l) == 2), "'utt2spk.txt' should contain only lines with two columns"
		utt_ids.append(l[0])
		speakers.append(l[1])
	return utt_ids, speakers


def copy_match(file_in, file_out, get_matches):
	with codecs.open(file_in, mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	lines = get_matches(lines)
	with codecs.open(file_out, mode='w', encoding='UTF-8') as out:
		for line in lines:
			out.write(line)


def train_test_split(corpus_path, split_speakers=False,
				train_amount=None,
				train_proportion=None,
				train_speakers=None,																	
				train_name="train", test_name="test"):
	"""
	Separate the utterances in a corpus in abkhazia format into
	a train set and a test set. The results are put in a subfolder
	of the 'data' directory of the corpus named 'split' 
	
	Only one of train_amount, train_proportion and train_speakers	
	can be set at the same time (default is train_proportion=0.5)
	train_speakers cannot be set if split_speakers is True
	
	If the split_speakers argument is False,
	the data for each speaker is attributed to one of the
	two sets as a whole.
	If train_speakers is set, it determines which speaker
	goes in which set. 
	Otherwise train_amount (or a proportion train_proportion)
	of the speakers are randomly selected to be in the
	training set. Note that this might not be appropriate
	when the amount of utterances available per speaker
	is too unbalanced.
	
	If the split_speakers argument is True,
	both sets get speech from all the speakers
	with a number of utterances by speaker in each set
	matching the number of utterances by speaker in the
	whole corpus.
	The total number of utterances in the training set
	is equal to either train_amount or 
	round(train_proportion*total_nb_utt).
	"""
	""" parse arguments """
	assert p.isdir(corpus_path), "{0} is not a directory".format(corpus_path)
	data_dir = p.join(corpus_path, 'data')
	assert p.isdir(data_dir), "{0} is not a directory".format(data_dir)
	split_dir = p.join(data_dir, 'split')
	if not(p.isdir(split_dir)):
		os.mkdir(split_dir)
	train_dir = p.join(split_dir, train_name)
	test_dir = p.join(split_dir, test_name)
	if p.isdir(train_dir):
		raise ValueError("There is already a split called: {0}".format(train_dir))	
	else:
		os.mkdir(train_dir)
	if p.isdir(test_dir):
		raise ValueError("There is already a split called: {0}".format(test_dir))
	else:
		os.mkdir(test_dir)
	# all we need is the utt2spk.txt file
	utt2spk_file = p.join(data_dir, 'utt2spk.txt')
	assert p.exists(utt2spk_file), "{0} file does not exist".format(utt2spk_file)
	sp = not(train_speakers is None)
	am = not(train_amount is None)
	pr = not(train_proportion is None)
	if (sp and am) or (sp and pr) or (am and pr):
		raise ValueError("Specify only one of train_amount, train_proportion and train_speakers")
	if not(sp) and not(am) and not(pr):
		pr = True
		train_proportion = .5
	""" read input """
	utt_ids, utt_speakers = read_utt2spk(p.join(corpus_path, 'data', 'utt2spk.txt'))
	utts = zip(utt_ids, utt_speakers)
	nb_utts = len(utt_ids)
	speakers =	set(utt_speakers)
	""" split utterances """
	train_utt_ids, test_utt_ids = [], []
	if split_speakers:
		assert not(sp), \
			"When split_speakers is set to True, the train_speakers argument cannot be used"
		proportion = train_proportion if pr else int(round(train_amount/float(nb_utts)))
		for speaker in speakers:
			spk_utts = \
				[utt_id for utt_id, utt_speaker in utts \
					if utt_speaker == speaker]
			assert len(spk_utts) > 1, \
				"Speaker {0} has only {1} sentence".format(speaker, len(spk_utts))
			n_train = int(round(len(spk_utts)*proportion))
			assert n_train < len(spk_utts), \
				(
				"Your choice of parameters yields a test set without any sentence "
				"from speaker {0}"
				).format(speaker)
			assert n_train > 0, \
				(
				"Your choice of parameters yields a train set without any sentence "
				"from speaker {0}"
				).format(speaker)
			# sample train and test utterances at random for this speaker
			train_utts = random.sample(spk_utts, n_train)
			test_utts = list(set.difference(set(spk_utts), set(train_utts)))
			# add to train and test sets
			train_utt_ids = train_utt_ids + train_utts
			test_utt_ids = test_utt_ids + test_utts
	else:
		if am or pr:
			amount = train_amount if am else int(round(train_proportion*len(speakers)))
			assert amount > 0, "Your choice of parameters yields an empty train-set"
			assert amount < len(speakers), "Your choice of parameters yields an empty test-set"
			speaker_list = list(speakers)
			random.shuffle(speaker_list)
			train_speakers = speaker_list[:amount]
		else:
			missing_speakers = [spk for spk in train_speakers if not(spk in speakers)]
			assert not(missing_speakers), \
				(
				"The following speakers specified in train_speakers "
				"are not found in the corpus: {0}"
				).format(missing_speakers)
		for speaker in speakers:
			spk_utts = \
				[utt_id for utt_id, utt_speaker in utts \
					if utt_speaker == speaker]
			if speaker in train_speakers:
				train_utt_ids = train_utt_ids + spk_utts
			else:
				test_utt_ids = test_utt_ids + spk_utts
	""" write output and cpp sort the files """
	files= ['utt2spk.txt', 'text.txt', 'segments.txt']
	try:
		# select relevant parts of utt2spk.txt, text.txt and segments.txt
		def match_utt_ids(lines, desired_utt_ids):
			utt_ids = [line.strip().split(u" ")[0] for line in lines]
			# need numpy here to get something fast easily
			# could also have something faster with pandas
			# see http://stackoverflow.com/questions/15939748/check-if-each-element-in-a-numpy-array-is-in-another-array
			indices = np.where(np.in1d(np.array(utt_ids), np.array(desired_utt_ids)))[0]
			lines = list(np.array(lines)[indices])		
			return lines
		match_train = lambda lines: match_utt_ids(lines, train_utt_ids)
		match_test = lambda lines: match_utt_ids(lines, test_utt_ids)
		for f in files:
			copy_match(p.join(data_dir, f), p.join(train_dir, f), match_train)
			copy_match(p.join(data_dir, f), p.join(test_dir, f), match_test)
			cpp_sort(p.join(train_dir, f))
			cpp_sort(p.join(test_dir, f))
	except:
		try:
			shutil.rmtree(train_dir)			
		except:
			pass
		try:
			shutil.rmtree(test_dir)			
		except:
			pass		
		raise
	
	
# test on buckeye for challenge
corpus_path = '/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/corpora/Buckeye'
buckeye_speakers = [
				u's08', u's09', u's01', u's02',
				u's03', u's04', u's05', u's06',
				u's07', u's36', u's35', u's34',
				u's40', u's37', u's31', u's19',
				u's18', u's39', u's38', u's13',
				u's12', u's11', u's10', u's17',
				u's16', u's15', u's14', u's33',
				u's32', u's30', u's22', u's23',
				u's20', u's21', u's26', u's27',
				u's24', u's25', u's28', u's29'
			]
test_speakers = [
			u's01', u's20', u's23', u's24',
			u's25', u's26', u's27', u's29',
			u's30', u's31', u's32', u's33'
			]
train_speakers = list(set.difference(set(buckeye_speakers), set(test_speakers)))
train_test_split(corpus_path, train_speakers=train_speakers, split_speakers=False)
