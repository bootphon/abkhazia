# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz
"""

"""
This script takes a corpus in abkhazia format
which has been splitted into a train and a test part
and instantiates a kaldi recipe to train
a standard speaker-adapted triphone HMM-GMM model
on the train part and output various kind of decodings
of the test part.

This script does not make any parameter fitting,
the user can provide his parameters, otherwise
default values are used.
"""
import shutil
import os.path as p
import os
import codecs
import subprocess

#TODO make smaller functions from this big file
#TODO: share this with validate_corpus

def remove_utt_ids(in_file, out_file):
	with codecs.open(out_file, mode='w', encoding='UTF-8') as out:
		for line in codecs.open(in_file, mode='r', encoding='UTF-8'):
			l = u' '.join(line.strip().split(u' ')[1:]) + u'\n'
			out.write(l)


def cpp_sort(filename):
	# there is redundancy here but I didn't check which export can be 
	# safely removed, so better safe than sorry
	os.environ["LC_ALL"] = "C"
	subprocess.call("export LC_ALL=C; sort {0} -o {1}".format(filename, filename), shell=True, env=os.environ)


def create_kaldi_recipe(corpus_path, output_path, kaldi_root,
					recipe_name="train_and_decode",																			
					train_name='train', test_name='test',
					si_params=None, sa_params=None):
	corpus_path = p.join(corpus_path, 'data')
	assert p.isdir(corpus_path), "Directory doesn't exist: {0}".format(corpus_path)
	train_path = p.join(corpus_path, 'split', train_name) 
	test_path = p.join(corpus_path, 'split', test_name)
	assert p.isdir(train_path), "Split doesn't exist: {0}".format(train_path)
	assert p.isdir(test_path), "Split doesn't exist: {0}".format(test_path)
	output_path = p.join(output_path, recipe_name, 's5')
	out_train = p.join(output_path, 'data', train_name)
	out_test = p.join(output_path, 'data', test_name)
	out_dict = p.join(output_path, 'data', 'local', 'dict')
	out_lm = p.join(output_path, 'data', 'local', 'lm')
	if p.isdir(output_path):
		raise IOError("Directory already exists: {0}".format(output_path))
	else:
		os.makedirs(output_path)
	for f in [out_train, out_test, out_dict, out_lm]:
		if not(p.isdir(f)):
			os.makedirs(f)
	## DICT folder (common to all splits)
	# lexicon.txt
	shutil.copy(p.join(corpus_path, 'lexicon.txt'), p.join(out_dict, 'lexicon.txt'))
	# phones.txt
	with codecs.open(p.join(corpus_path, 'phones.txt'), mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	with codecs.open(p.join(out_dict, 'nonsilence_phones.txt'), mode='w', encoding='UTF-8') as out:
		for line in lines:
			symbol = line.split(u' ')[0]
			out.write(u"{0}\n".format(symbol))
	# silences.txt
	shutil.copy(p.join(corpus_path, 'silences.txt'), p.join(out_dict, 'silence_phones.txt'))	
	with codecs.open(p.join(out_dict, 'optional_silence.txt'), mode='w', encoding='UTF-8') as out:
		out.write(u'SIL\n')
	# variants.txt
	shutil.copy(p.join(corpus_path, 'variants.txt'), p.join(out_dict, 'extra_questions.txt'))
	## Data folders (split specific)
	for split_in, split_out in zip([train_path, test_path], [out_train, out_test]):
		# text.txt
		shutil.copy(p.join(split_in, 'text.txt'), p.join(split_out, 'text'))
		# utt2spk.txt
		shutil.copy(p.join(split_in, 'utt2spk.txt'), p.join(split_out, 'utt2spk'))
		# segments
		with codecs.open(p.join(split_in, 'segments.txt'), mode='r', encoding='UTF-8') as inp:
			lines = inp.readlines()
		with codecs.open(p.join(split_out, 'segments'), mode='w', encoding='UTF-8') as out:
			wavs = set()
			for line in lines:
				utt_id, wav_id, start, stop = line.strip().split(u' ')
				record_id = p.splitext(wav_id)[0]
				out.write(u"{0} {1} {2} {3}\n".format(utt_id, record_id, start, stop))
				wavs.add(wav_id)
		## wav.scp
		wav_scp = p.join(split_out, 'wav.scp')
		with codecs.open(wav_scp, mode='w', encoding='UTF-8') as out_w:
			for wav_id in wavs:
				record_id = p.splitext(wav_id)[0]
				wav_full_path = p.join(p.abspath(output_path), 'wavs', wav_id)
				out_w.write(u"{0} {1}\n".format(record_id, wav_full_path))
		# do some cpp_sorting just to be sure (for example if abkhazia corpus has
		# been copied to a different machine after its creation, there might be 
		# some machine-dependent differences in the required orders)
		files = ['text', 'utt2spk', 'segments', 'wav.scp']
		for f in files:
			cpp_sort(p.join(split_out, f))
	# create transcripts without utt-ids for LM estimation
	#FIXME make this coherent with kaldi recipe
	train_lm = p.join(out_lm, 'train_lm.txt')
	test_lm =p.join(out_lm, 'test_lm.txt')
	for in_dir, out_file in zip([out_train, out_test], [train_lm, test_lm]):
		remove_utt_ids(p.join(in_dir, 'text'), out_file)
	# wav folder (common to all splits)
	link_name =  p.join(output_path, 'wavs')
	target = p.join(corpus_path, 'wavs')
	if p.exists(link_name):
		os.remove(link_name)
	os.symlink(target, link_name)
	# kaldi symlinks, directories and files
	steps_dir = p.abspath(p.join(kaldi_root, 'egs', 'wsj', 's5', 'steps'))
	steps_link = p.abspath(p.join(output_path, 'steps'))
	if p.exists(steps_link):
		os.remove(steps_link)
	utils_dir = p.abspath(p.join(kaldi_root, 'egs', 'wsj', 's5', 'utils'))
	utils_link = p.abspath(p.join(output_path, 'utils'))
	if p.exists(utils_link):
		os.remove(utils_link)
	subprocess.call("ln -s {0} {1}".format(steps_dir, steps_link), shell=True)
	subprocess.call("ln -s {0} {1}".format(utils_dir, utils_link), shell=True)
	conf_dir = p.join(output_path, 'conf')	
	if p.exists(conf_dir):
		shutil.rmtree(conf_dir)
	os.mkdir(conf_dir)
	with open(p.join(conf_dir, 'mfcc.conf'), mode='w') as out:
		pass
	# cmd, path, score
	kaldi_bin_dir = p.dirname(p.realpath(__file__))
	kaldi_dir = p.join(kaldi_bin_dir, '..', '..', 'kaldi')
	cmd_file = p.join(kaldi_dir, 'cmd.sh')
	if not(p.exists(cmd_file)):
		raise IOError(
			(
			"No cmd.sh in {0} "
			"You need to create one adapted to "
			"your machine. You can get inspiration "
			"from {1}"
			).format(kaldi_dir, p.join(kaldi_bin_dir, 'cmd_template.sh'))
		)
	shutil.copy(cmd_file, p.join(output_path, 'cmd.sh'))
	path_file = p.join(kaldi_dir, 'path.sh')
	if not(p.exists(path_file)):
		raise IOError(
			(
			"No path.sh in {0} "
			"You need to create one adapted to "
			"your machine. You can get inspiration "
			"from {1}"
			).format(kaldi_dir, p.join(kaldi_bin_dir, 'path_template.sh'))
		)
	shutil.copy(path_file, p.join(output_path, 'path.sh'))
	score_file = p.join(kaldi_dir, 'score.sh')
	if not(p.exists(score_file)):
		raise IOError(
			(
			"No score.sh in {0} "
			"You need to create one adapted to "
			"your machine. You can get inspiration "
			"from {1}"
			).format(kaldi_dir, p.join(kaldi_bin_dir, 'score_template.sh'))
		)
	local_dir = p.join(output_path, 'local')
	if not(p.isdir(local_dir)):
		os.mkdir(local_dir)
	shutil.copy(score_file, p.join(local_dir, 'score.sh'))
	## last missing piece run.sh
	#TODO
	if si_params is None:
		pass
	if sa_params is None:
		pass
	
#TODO: then need to run the recipe and parse the results to either .txt or .features format

#root = '/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia'
#kaldi_root = '/Users/thomas/Documents/PhD/Recherche/kaldi/kaldi-trunk'
root = '/fhgfs/bootphon/scratch/thomas/abkhazia'
kaldi_root = '/fhgfs/bootphon/scratch/thomas/kaldi'
#create_kaldi_recipe(p.join(root, 'corpora', 'Buckeye'), p.join(root, 'kaldi', 'Buckeye'), kaldi_root)
create_kaldi_recipe(p.join(root, 'corpora', 'NCHLT_Tsonga'), p.join(root, 'kaldi', 'NCHLT_Tsonga'), kaldi_root)
