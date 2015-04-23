# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz
"""


def get_dict_path(recipe_path):
	dict_path = p.join(recipe_path, 'data', 'local', 'dict')
	if not(p.isdir(dict_path)):
			os.makedirs(dict_path)
	return dict_path


def setup_lexicon(corpus_path, recipe_path, prune_lexicon=False, train_name=None):
	dict_path = get_dict_path(recipe_path)
	if prune_lexicon:
		# get words appearing in train part
		train_text = p.join(corpus_path, 'data', 'split', train_name, 'text.txt')
		_, utt_words = io.read_text(train_text)
		allowed_words = list(set([word for utt in utt_words for word in utt]))
		# remove other words from the lexicon
		io.copy_first_col_matches(p.join(corpus_path, 'data', 'lexicon.txt'),
								  p.join(dict_path, 'lexicon.txt'),
								  allowed_words)
	else:
		shutil.copy(p.join(corpus_path, 'data', 'lexicon.txt'),
					p.join(dict_path, 'lexicon.txt'))
		

def setup_phones(corpus_path, recipe_path):
	dict_path = get_dict_path(recipe_path)
	with codecs.open(p.join(corpus_path, 'data', 'phones.txt'),
					 mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	with codecs.open(p.join(dict_path, 'nonsilence_phones.txt'),
					 mode='w', encoding='UTF-8') as out:
		for line in lines:
			symbol = line.split(u' ')[0]
			out.write(u"{0}\n".format(symbol))


def setup_silences(corpus_path, recipe_path):
	dict_path = get_dict_path(recipe_path)
	shutil.copy(p.join(corpus_path, 'data', 'silences.txt'),
				p.join(dict_path, 'silence_phones.txt'))	
	with codecs.open(p.join(dict_path, 'optional_silence.txt'),
					 mode='w', encoding='UTF-8') as out:
		out.write(u'SIL\n')


def setup_variants(corpus_path, recipe_path):
	dict_path = get_dict_path(recipe_path)
	shutil.copy(p.join(corpus_path, 'data', 'variants.txt'),
				p.join(dict_path, 'extra_questions.txt'))


def get_data_path(corpus_path, recipe_path, in_split=None, out_split=None):
	if in_split is None:
		inp = p.join(corpus_path, 'data')
	else:
		inp = p.join(corpus_path, 'data', 'split', in_split)
	assert p.isdir(inp), "Directory doesn't exist: {0}".format(inp)
	if out_split is None:
		out = p.join(recipe_path, 'data', 'main')
	else:
		out = p.join(recipe_path, 'data', out_split)
	if not(p.isdir(out)):
		os.makedirs(out)
	return inp, out


def setup_text(corpus_path, recipe_path, in_split=None, out_split=None, desired_utts=None):
	i_path, o_path = get_data_path(corpus_path, recipe_path, in_split, out_split)
	if desired_utts is None:
		shutil.copy(p.join(i_path, 'text.txt'), p.join(o_path, 'text'))
	else:
		io.copy_first_col_matches(p.join(i_path, 'text.txt'),
							  	  p.join(o_path, 'text'),
							  	  desired_utts)


def setup_utt2spk(corpus_path, recipe_path, in_split=None, out_split=None, desired_utts=None):
	i_path, o_path = get_data_path(corpus_path, recipe_path, in_split, out_split)
	if desired_utts is None:
		shutil.copy(p.join(i_path, 'utt2spk.txt'), p.join(o_path, 'utt2spk'))
	else:
		io.copy_first_col_matches(p.join(i_path, 'utt2spk.txt'),
							  	  p.join(o_path, 'utt2spk'),
							  	  desired_utts)


def	setup_segments(corpus_path, recipe_path, in_split=None, out_split=None, desired_utts=None):	
	i_path, o_path = get_data_path(corpus_path, recipe_path, in_split, out_split)
	with codecs.open(p.join(i_path, 'segments.txt'),
					 mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	# write only if starts and stops are specified in segments.txt
	if len(lines[0].strip().split(u" ")) == 4:
		if not(desired_utts is None):
			# select utterances that are long enough (>= 15 ms)
			lines = io.match_utt_ids(lines, desired_utts)
		with codecs.open(p.join(o_path, 'segments'),
						 mode='w', encoding='UTF-8') as out:
			for line in lines:
				elements = line.strip().split(u" ")
				utt_id = elements[0]
				record_id = p.splitext(wav_id)[0]
				out.write(u" ".join([utt_id, record_id] + elements[2:]) + u"\n")


def setup_wav(corpus_path, recipe_path, in_split=None, out_split=None, desired_utts=None):
	i_path, o_path = get_data_path(corpus_path, recipe_path, in_split, out_split)
	# get list of wavs from segments.txt
	with codecs.open(p.join(i_path, 'segments.txt'),
					 mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	if not(desired_utts is None):
		# select utterances that are long enough (>= 15 ms)
		lines = io.match_utt_ids(lines, desired_utts) 
	wavs = set()
	for line in lines:
		elements = line.strip().split(u" ")
		wav_id = elements[1]
		wavs.add(wav_id)
	# write wav.scp 
	with codecs.open(p.join(o_path, 'wav.scp'),
					 mode='w', encoding='UTF-8') as out:
		for wav_id in wavs:
			record_id = p.splitext(wav_id)[0]
			wav_full_path = p.join(p.abspath(recipe_path), 'wavs', wav_id)
			out.write(u"{0} {1}\n".format(record_id, wav_full_path))


def setup_wav_folder(corpus_path, recipe_path):
	# using a symbolic link to avoid copying
	# voluminous data
	link_name = p.join(recipe_path, 'wavs')
	target = p.join(corpus_path, 'data', 'wavs')
	if p.exists(link_name):
		# could log this...
		os.remove(link_name)
	os.symlink(target, link_name)


def setup_kaldi_folder(kaldi_root, recipe_path):
	steps_dir = p.abspath(p.join(kaldi_root, 'egs', 'wsj', 's5', 'steps'))
	steps_link = p.abspath(p.join(recipe_path, 'steps'))
	if p.exists(steps_link):
		os.remove(steps_link)
	utils_dir = p.abspath(p.join(kaldi_root, 'egs', 'wsj', 's5', 'utils'))
	utils_link = p.abspath(p.join(recipe_path, 'utils'))
	if p.exists(utils_link):
		os.remove(utils_link)
	subprocess.call("ln -s {0} {1}".format(steps_dir, steps_link), shell=True)
	subprocess.call("ln -s {0} {1}".format(utils_dir, utils_link), shell=True)
	conf_dir = p.join(recipe_path, 'conf')	
	if p.exists(conf_dir):
		shutil.rmtree(conf_dir)
	os.mkdir(conf_dir)
	# create mfcc.conf file (following what seems to be commonly used in other kaldi recipes)
	with open(p.join(conf_dir, 'mfcc.conf'), mode='w') as out:
		out.write("--use-energy=false   # only non-default option.\n")


def copy_template(filename, template, recipe_path):
	d, f = p.split(filename)
	if not(p.exists(filename)):
		raise IOError(
			(
			"No {0} in {1} "
			"You need to create one adapted to "
			"your machine. You can get inspiration "
			"from {2}"
			).format(f, d, template)
		)
	shutil.copy(filename, p.join(recipe_path, f))


def setup_machine_specific_scripts(recipe_path):
	kaldi_bin_dir = p.dirname(p.realpath(__file__))
	kaldi_dir = p.join(kaldi_bin_dir, '..', '..', 'kaldi')
	cmd_file = p.join(kaldi_dir, 'cmd.sh')
	cmd_template = p.join(kaldi_bin_dir, 'kaldi_templates', 'cmd_template.sh')
	copy_template(cmd_file, cmd_template, recipe_path)
	path_file = p.join(kaldi_dir, 'path.sh')
	path_template = p.join(kaldi_bin_dir, 'kaldi_templates', 'path_template.sh')
	copy_template(path_file, path_template, recipe_path)


def setup_main_scripts(recipe_path):
	kaldi_bin_dir = p.dirname(p.realpath(__file__))
	# score.sh
	score_file = p.join(kaldi_bin_dir, 'kaldi_templates', 'standard_score.sh')
	local_dir = p.join(recipe_path, 'local')
	if not(p.isdir(local_dir)):
		os.mkdir(local_dir)
	shutil.copy(score_file, p.join(local_dir, 'score.sh'))
	# run.sh
	run_file = p.join(kaldi_bin_dir, 'kaldi_templates', 'train_and_decode.sh')
	shutil.copy(run_file, p.join(recipe_path, 'run.sh'))
