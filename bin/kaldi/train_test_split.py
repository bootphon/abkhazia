
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
	
	
# test on Buckeye for challenge
"""
corpus_path = '/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/corpora/Buckeye'
all_speakers = [
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
train_speakers = list(set.difference(set(all_speakers), set(test_speakers)))
train_test_split(corpus_path, train_speakers=train_speakers, split_speakers=False)
"""

# test on NCHLT_Tsonga for challenge

corpus_path = '/fhgfs/bootphon/scratch/thomas/abkhazia/corpora/NCHLT_Tsonga'
all_speakers = [
			u'149f', u'021m', u'084m', u'131f',
			u'109f', u'506f', u'179m', u'130m',
			u'103f', u'012m', u'115f', u'004f',
			u'122f', u'166m', u'141m', u'033f',
			u'060m', u'092m', u'106m', u'053f',
			u'182f', u'072m', u'043f', u'083f',
			u'167m', u'177m', u'507f', u'502f',
			u'172f', u'013m', u'003f', u'023f',
			u'178f', u'114m', u'063f', u'030m',
			u'146f', u'014m', u'093m', u'054f',
			u'042f', u'073m', u'183m', u'086m',
			u'135m', u'505m', u'090m', u'046f',
			u'126f', u'010m', u'026f', u'154m',
			u'113m', u'123m', u'133f', u'500m',
			u'148f', u'098m', u'153f', u'045m',
			u'074m', u'059m', u'019f', u'066f',
			u'164f', u'029m', u'035f', u'051f',
			u'143m', u'184f', u'156f', u'151m',
			u'085f', u'138m', u'069m', u'107f',
			u'011f', u'134m', u'104f', u'108m',
			u'005f', u'112f', u'132m', u'061m',
			u'101m', u'150m', u'075m', u'044f',
			u'020m', u'165f', u'140f', u'099m',
			u'032f', u'052f', u'091m', u'028f',
			u'118m', u'173f', u'171m', u'159m',
			u'152m', u'186m', u'096m', u'024f',
			u'016m', u'116m', u'048f', u'121m',
			u'076m', u'174m', u'120f', u'088m',
			u'057f', u'110m', u'007m', u'501m',
			u'037m', u'162f', u'047m', u'080f',
			u'064m', u'145m', u'155m', u'187f',
			u'190m', u'087m', u'170f', u'097m',
			u'027f', u'503m', u'017m', u'175f',
			u'068f', u'006m', u'058m', u'067f',
			u'077m', u'018f', u'034f', u'163f',
			u'139f', u'102f', u'142m', u'144m',
			u'050f', u'158f', u'188m', u'125m',
			u'504f', u'078m', u'094f', u'038f',
			u'022m', u'117m', u'127f', u'002m',
			u'136f', u'009m', u'157m', u'055m',
			u'062m', u'031f', u'015m', u'176f',
			u'070f', u'147m', u'180f', u'161m',
			u'041f', u'128m', u'082f', u'160f',
			u'137m', u'095m', u'079f', u'189f',
			u'100m', u'039m', u'001m', u'025f',
			u'049f', u'169f', u'008m', u'111f',
			u'056f', u'089m', u'168f', u'129f',
			u'071f', u'081m', u'124m', u'185f',
			u'040f', u'065f', u'181m', u'119f', 
			u'105m', u'036f'
			]

test_speakers = [
			u'130m', u'139f', u'132m', u'102f',
			u'128m', u'103f', u'146f', u'134m',
			u'104f', u'135m', u'141m', u'001m',
			u'142m', u'131f', u'126f', u'143m',
			u'138m', u'127f', u'144m', u'133f',
			u'145m', u'129f', u'140f', u'136f'
			]
train_speakers = list(set.difference(set(all_speakers), set(test_speakers)))
train_test_split(corpus_path, train_speakers=train_speakers, split_speakers=False)
