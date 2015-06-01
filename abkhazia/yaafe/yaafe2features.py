"""
Created on Mon Dec  1 15:05:38 2014

@author: Thomas Schatz

This module requires:
	- numpy
	- h5features (https://github.com/bootphon/h5features)
	- yaafelib
"""


# see: http://yaafe.sourceforge.net/manual/tools.html#python-interaction
import yaafelib as ya
import numpy as np
import h5features
import os.path as p
import abkhazia.utilities.basic_io as io


def yaafe2features(wavefiles, out_file):
	"""
	Generate features with yaafe and put them in h5features format.

	Whole wavefiles are encoded as internal h5features files.
	To use them with abkhazia's ABX tasks, these need to be segmented
	according to an abkhazia segments.txt 
	(abkhazia/utilities/segment_features.py can be used for this)

	For now only option is MFCC features
	"""
	fp = ya.FeaturePlan(sample_rate=16000)
	fp.addFeature('mfcc: MFCC blockSize=400 stepSize=160')  # 0.025s + 0.01s
	df = fp.getDataFlow()

	engine = ya.Engine()
	engine.load(df)

	wav_ids = []
	times = []
	features = []
	for wavefile in wavefiles:
		wav_ids.append(p.splitext(p.basename(wavefile))[0])
		afp = ya.AudioFileProcessor()
		afp.processFile(engine, wavefile)
		mfcc = engine.readAllOutputs()['mfcc']
		nframes = mfcc.shape[0]
		# times according to: http://yaafe.sourceforge.net/features.html?highlight=mfcc#yaafefeatures.Frames
		times.append(0.01*np.arange(nframes))  # 0.01 here is ad hoc and dependent on 160 above
		features.append(mfcc)
	h5features.write(out_file, 'features', wav_ids, times, features)


def encode_corpus(corpus, split='test'):
	"""
	Generates yaafe features (in h5features format) for the 'test' part of a
	standard train/test split of an abkhazia corpus. The features are ready for
	use in abkhazia's ABX tasks. 
	"""
	segments_file = p.join(corpus, 'data', 'split', split, 'segments.txt')
	_, wavefiles, _, _ = io.read_segments(segments_file)
	wavefiles = [p.join(corpus, 'data', 'wavs', wavefile) for wavefile in set(wavefiles)]
	features_dir = p.join(corpus, 'data', 'features')
	if not(os.path.isdir(features_dir)):
		os.mkdir(features_dir)
	out_file = p.join(corpus, 'data', 'features', 'yaafe_MFCC.features')
	yaafe2features(wavefiles, out_file)


# test
root = '/fhgfs/bootphon/scratch/thomas/abkhazia/corpora'
corpus = p.join(root, 'WSJ_main_read')
encode_corpus(corpus)


"""
Installing yaafe can be tricky. 
On our linux cluster (Oberon), a yaafe module is available.

Here are some installation notes for MacOS:

On OSX Snow Leopard with homebrew:
	brew install argtable
	brew install libsndfile
	brew install mpg123
	brew install fftw
	download Yaafe repository from sourceforge (not github): http://sourceforge.net/projects/yaafe/files/yaafe-v0.64.tgz/download
	cd to yaafe-v0.64
	mkdir ../yaafe
	mkdir build
	cd build
	cmake -DCMAKE_INSTALL_PREFIX=../../yaafe -DWITH_MPG123=ON ..
	#maybe cmake -DCMAKE_INSTALL_PREFIX=../../yaafe .. works just as well
	make
	make install

	Then to use yaafe:
		export INSTALL_DIR="/Users/thomas/Documents/PhD/Recherche/Code/yaafe"
		export YAAFE_PATH=$INSTALL_DIR/yaafe_extensions
		export PATH=$PATH:$INSTALL_DIR/bin
		export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:$INSTALL_DIR/lib
		export PYTHONPATH=$PYTHONPATH:$INSTALL_DIR/python_packages
		(with spyder, needs to be done before launching spyder)

On OSX Yosemite with homebrew: older sourceforge version did not work,
had to use github version (which did not work on Snow Leopard)
	Same as before (or just brew upgrade if already installed): 
		brew install argtable
		brew install libsndfile
		brew install mpg123
		brew install fftw
	Then:
		git clone https://github.com/Yaafe/Yaafe.git
		cd Yaafe
		mkdir ../yaafe_install
		git submodule init  # to prepare Eigen code under the externals directory
		git submodule update
		mkdir build
		cd build
		cmake -DCMAKE_INSTALL_PREFIX=../../yaafe_install -DWITH_MPG123=ON ..
		#maybe cmake -DCMAKE_INSTALL_PREFIX=../../yaafe_install .. works just as well
		make
		make install
	Then to use yaafe:
		export INSTALL_DIR="/Users/thomas/Documents/PhD/Recherche/Code/yaafe_install"
		export PATH=$PATH:$INSTALL_DIR/bin
		export YAAFE_PATH=$INSTALL_DIR/lib/python2.7/site-packages
		export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:$INSTALL_DIR/lib
		export PYTHONPATH=$PYTHONPATH:$INSTALL_DIR/lib/python2.7/site-packages
		(with spyder, needs to be done before launching spyder)
"""