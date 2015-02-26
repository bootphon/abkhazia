# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""

"""
This script checks whether a given speech corpus is correctly formatted 
for usage with abkhazia tools
"""

import contextlib
import logging
import os
import wave
import numpy as np
import codecs


def validate(corpus_path):

	"""
	Check corpus directory structure
	"""
	data_dir = os.path.join(corpus_path, 'data')
	if not(os.path.isdir(data_dir)):
		raise IOError("Corpus folder {0} should contain a 'data' subfolder".format(corpus_path))
	log_dir = os.path.join(corpus_path, 'logs')
	if not(os.path.isdir(log_dir)):
		raise IOError("Corpus folder {0} should contain a 'logs' subfolder".format(corpus_path))	
	
	# log file config
	log = logging.getLogger()
	log.setLevel(logging.DEBUG)
	log_file = os.path.join(log_dir, "data_validation.log".format(corpus_path))
	log_handler = logging.FileHandler(log_file, mode='w')
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	log_handler.setFormatter(formatter)
	log_handler.setLevel(logging.DEBUG)
	log.addHandler(log_handler)


	"""
	wav directory must contain only mono wavefiles in 16KHz, 16 bit PCM format
	"""
	log.info("Checking 'wavs' folder")
	wav_dir = os.path.join(data_dir, 'wavs')
	files = os.listdir(wav_dir)
	l = [f[-4:] == ".wav" for f in files]
	if not(all(l)):
		f = files[np.where(np.logical_not(l))[0][0]]
		raise IOError("file {0} in 'wavs' folder doesn't have a '.wav' extension".format(f))
	for f in files:
		filepath = os.path.join(wav_dir, f)
		with contextlib.closing(wave.open(filepath,'r')) as fh:
			(nb_channels, width, rate, nframes, comptype, compname) = fh.getparams()
	    	if nframes == 0:
	    		log.warning('File {0} is empty'.format(f))
	    	if rate != 16000:
	    		raise IOError('Currently only files sampled at 16,000 Hz are supported. \
	    						File {0} is sampled at {1} Hz'.format(f, rate))
	    	if nb_channels != 1:
	    		raise IOError('File {0} has {1} channels, only files with 1 channel \
	    						are currently supported'.format(f, nb_channels))
	    	if width != 2:  # in bytes: 16 bit == 2 bytes
	    		raise IOError('File {0} is encoded on {1} bits, only files encoded \
	    						on 16 bits are currently supported'.format(f, 8*width))
	    	if comptype != 'NONE':
	    		raise IOError('File {0} is compressed'.format(f))
    	log.info("'wavs' folder is OK")


	"""
	checking utterance list
	"""
	with codecs.open(os.path.join(data_dir, "text"), mode='r', encoding="UTF-8"):
		
	# unique utterance-ids
		
	
	#Add check: main dict: no more than one pronunciation by word

	#Change extra_questions to use original encoding? what about xsampa? we let it as an option but not mandatory