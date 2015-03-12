# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz
"""

"""
This script takes a corpus in abkhazia format
and instantiates a kaldi recipe to train
a standard speaker-adapted triphone HMM-GMM model
on this corpus and output a forced alignment
of it.

This script does not make any parameter fitting,
the user can provide his parameters, otherwise
default values are used.
"""

#TODO: this script is not ready as is and need correction and completion
import shutil
import os.path as p
import os
import codecs
import subprocess


#TODO: share this with validate_corpus
def cpp_sort(filename):
	# there is redundancy here but I didn't check which export can be 
	# safely removed, so better safe than sorry
	os.environ["LC_ALL"] = "C"
	subprocess.call("export LC_ALL=C; sort {0} -o {1}".format(filename, filename), shell=True, env=os.environ)


def create_kaldi_recipe(corpus_path, output_path, kaldi_root, 
					train_name='train', test_name='test'):
	output_path = p.join(output_path, 's5')
	corpus_path = p.join(corpus_path, 'data')
	out_main = p.join(output_path, 'data', 'main')
	out_dict = p.join(output_path, 'data', 'local', 'dict')
	assert p.isdir(corpus_path), 'No such directory {0}'.format(corpus_path)
	if not(p.isdir(output_path)):
		os.makedirs(output_path)
	if not(p.isdir(out_main)):
		os.makedirs(out_main)
	if not(p.isdir(out_dict)):
		os.makedirs(out_dict)
	## DICT folder
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
	## MAIN folder	
	# text.txt
	shutil.copy(p.join(corpus_path, 'text.txt'), p.join(out_main, 'text'))
	# utt2spk.txt
	shutil.copy(p.join(corpus_path, 'utt2spk.txt'), p.join(out_main, 'utt2spk'))
	# segments
	with codecs.open(p.join(corpus_path, 'segments.txt'), mode='r', encoding='UTF-8') as inp:
		lines = inp.readlines()
	with codecs.open(p.join(out_main, 'segments'), mode='w', encoding='UTF-8') as out_s:
		wavs = set()
		for line in lines:
			utt_id, wav_id, start, stop = line.strip().split(u' ')
			record_id = p.splitext(wav_id)[0]
			out_s.write(u"{0} {1} {2} {3}\n".format(utt_id, record_id, start, stop))
			wavs.add(wav_id)
	# wav.scp
	wav_scp = p.join(out_main, 'wav.scp')
	with codecs.open(wav_scp, mode='w', encoding='UTF-8') as out_w:
		for wav_id in wavs:
			record_id = p.splitext(wav_id)[0]
			wav_full_path = p.join(p.abspath(output_path), 'wavs', wav_id)
			out_w.write(u"{0} {1}\n".format(record_id, wav_full_path))
	cpp_sort(p.join(out_main, 'wav.scp'))
	# wav folder
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


root = '/fhgfs/bootphon/scratch/thomas/abkhazia'
kaldi_root = '/fhgfs/bootphon/scratch/thomas/kaldi'
convert(p.join(root, 'corpora', 'Buckeye'), p.join(root, 'kaldi', 'Buckeye'), kaldi_root)
