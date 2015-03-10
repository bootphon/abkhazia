# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz
"""

"""
This script converts a corpus in abkhazia format to standard kaldi format
"""
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


def convert(corpus_path, output_path):
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
			utt_id, wav_id, start, stop = line.split(u' ')
			record_id = p.splitext(wav_id)[0]
			out_s.write(u"{0} {1} {2} {3}\n".format(utt_id, record_id, start, stop))
			wavs.add(wav_id)
	# wav.scp
	wav_scp = p.join(out_main, 'wav.scp')
	with codecs.open(wav_scp, mode='w', encoding='UTF-8') as out_w:
		for wav_id in wavs:
			wav_full_path = p.join(p.abspath(output_path), 'wavs', wav_id)
			out_w.write(u"{0} {1}\n".format(record_id, wav_full_path))
	cpp_sort(p.join(output_path, 'wav.scp'))
	# wav folder
	link_name =  p.join(output_path, 'wavs')
	target = p.join(corpus_path, 'wavs')
	if p.exists(link_name):
		os.remove(link_name)
	os.symlink(target, link_name)

root = '/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia'
convert(p.join(root, 'corpora', 'Buckeye'), p.join(root, 'kaldi', 'Buckeye'))