# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
Data preparation LibriSpeech
"""

import os
import subprocess as sp
import codecs
import re
import importlib
import logging
import shutil
import argparse
import sys



# path to a directory containing the Librispeech corpus	
raw_path = "/fhgfs/bootphon/data/raw_data/LibriSpeech/"



#######################################################################################
#######################################################################################
############################### Some utility functions ################################
#######################################################################################
#######################################################################################


# filter out .DS_Store files from MacOS if any
def list_dir(d):
	return [e for e in os.listdir(d) if e != '.DS_Store']

def copy_flac(i, o):
	input_dir = os.path.join(raw_path, i)
	print input_dir
	output_dir = os.path.join(raw_path, o)
	print output_dir
	for dirpath, dirs, files in os.walk(input_dir):
		#print dirpath
		#print dirs
		#print files
		for filename in files:
			if filename.endswith('.flac'):
				print "found extension"
				shutil.copy2(os.path.join(dirpath, filename), output_dir)

#needs 16-bit PCM wav format sampled at 16KHz
def convert_flac (i, o):
	fs = 16000  # sampling frequency of the input files in Hz
	nbits = 16  # each sample is coded on 16 bit in the input files
	input_dir = os.path.join(raw_path, i)
	output_dir = os.path.join(raw_path, o)
	flacs = list_dir(input_dir)
	for flac in flacs:
		raw = flac.replace('.flac', '.raw')
		wav = raw.replace('.raw', '.wav')
		#flac_file = os.path.join(input_dir, flac)
		raw_file = os.path.join(input_dir, raw)
		wav_file = os.path.join(output_dir, wav)
		sp.call("shorten -x {0} {1}".format(flac_file, raw_file), shell=True)
		sp.call("sox -t raw  -r {0} -e signed-integer -b {1} {2} -t wav {3}".format(fs, nbits, raw_file, wav_file), shell=True)
		os.remove(raw_file)
#copy_flac('train-clean-100', 'flac_train-clean-100')
convert_flac('flac_train-clean-100', 'wav_train-clean-100')


