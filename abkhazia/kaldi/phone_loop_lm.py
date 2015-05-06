
import os.path as p
import codecs
import shutil
import abkhazia.kaldi.abkhazia2kaldi as a2k 

# generate a phone-loop language model for use in kaldi
# for now each phone has equal probability (no phonotactics)

# acoustic models has context variants as well as word-position dependent variants, 
# can this cause a problem when using a simple phone loop? Would a model without the word-position
# dependent variants fare better?

# put this in a2k as setup_phone_loop ?
# control for risk of overwriting of lang and split in recipe/data ?

def setup_phone_loop(corpus_path, recipe_path, name="phone_loop"):
	"""
	recipe_path: e.g. "/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/kaldi/GP_Mandarin/train_and_decode/s5"
	lang_dir: e.g. "phone_loop"
			Will copy kaldi template'phone_loop_lm.sh' in 'recipe_path/local'
			and create a directory 'recipe_path/data/local/name'
			that can be passed as an argument to 'phone_loop_lm.sh'
			'phone_loop_lm.sh' can then be called to create a directory
			'recipe_path/data/name' that can be passed as the 'lm' argument
			to 'train_and_decode.sh'.
	"""
	# copy kaldi template'phone_loop_lm.sh' in 'recipe_path/local'
	kaldi_bin_dir = p.dirname(p.realpath(__file__))
	shutil.copy(p.join(kaldi_bin_dir, 'kaldi_templates', 'phone_loop_lm.sh'),\
				p.join(recipe_path, 'local', 'phone_loop_lm.sh'))
	
	# setup lang folder for phone loop with phones 
	a2k.setup_phones(corpus_path, recipe_path, name)  # nonsilence_phones.txt
	a2k.setup_silences(corpus_path, recipe_path, name)  # silence_phones.txt, optional_silence.txt
	a2k.setup_variants(corpus_path, recipe_path, name)  # extra_questions.txt
	# get list of phones
	with codecs.open(p.join(recipe_path, 'data', 'local', 'name', 'phones.txt'),\
					 mode='r', encoding="UTF-8") as inp:
		lines = inp.readlines()
	phones = [line.strip().split(u" ")[0] for line in lines]
	# add 'phone' lexicon
	with codecs.open(p.join(recipe_path, 'data', 'local', 'name', 'lexicon.txt'),\
					 mode='w', encoding="UTF-8") as out:
		for word in phones:
			out.write(u'{0} {1}\n'.format(word, word))
		out.write(u"<unk> SPN\n")  # is this right ?
		# should we add <noise> NSN, etc ??? depends on corpus though...
	# describe FST corresponding to desired language model in a text file
	with codecs.open(p.join(recipe_path, 'data', 'local', 'name', 'G.txt'),\
					 mode='w', encoding="UTF-8") as out:
		for word in phones:
			out.write(u'0 1 {0} {1}\n'.format(word, word))
		out.write(u'1 0.0')  # final node
	# note that optional silences are added when composing G with L (lexicon) 
	# when calling prepare_lang.sh, except if silence_prob is set to 0
