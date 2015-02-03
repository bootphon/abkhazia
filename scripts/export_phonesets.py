# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 14:20:27 2015

@author: Thomas Schatz
"""

# Possible improvements: 
# 	display order: sort based on articulatory features when possible
#	use load_phoneset inside phonesets2table

import codecs
import os
import operator


def phonesets2table(output_file, phonesets_files, phonesets=None, group_order=None):
	"""
	Create a nice dokuwiki table given one or several phonesets for a given language
	where phoneset files are in the format defined at:
	See:
		http://cogito.ens.fr/dokuwiki/doku.php?id=science:teams:models:abkhazia:abx-kaldi-standard-analyses&#phone_inventory
	"""
	with codecs.open(output_file, mode='w', encoding='utf-8') as out:
		if phonesets is None:
			phonesets = [os.path.splitext(os.path.basename(f)) for f in phonesets_files]
		# load content of input files
		phonesets_data = {}
		for phoneset_file, phoneset in zip(phonesets_files, phonesets):
			with codecs.open(phoneset_file, mode='r', encoding='utf_8') as inp:
				lines = inp.readlines()
				assert len(lines) % 2 == 0, \
					"Invalid structure file {0}: number of lines should be even".format(phoneset_file)
				phonesets_data[phoneset] = lines
		# parse content into groups for each phoneset
		phonesets_groups = {}
		for phoneset in phonesets:
			lines = phonesets_data[phoneset]
			groups = {}
			for i in range(len(lines)//2):
				groups[lines[2*i][:-1]] = lines[2*i+1][:-1]  # remove newline characters
			phonesets_groups[phoneset] = groups
		# fuse groups across phonesets
		all_groups = set()
		for groups in phonesets_groups:			
			all_groups = set.union(all_groups, {g for g in phonesets_groups[groups]})
		if group_order is None:
			group_order = all_groups
		groups = {}
		for group in all_groups:
			groups[group] = {}
			for phoneset in phonesets:
				try:
					groups[group][phoneset] = phonesets_groups[phoneset][group]
				except KeyError:
					groups[group][phoneset] = u''
		# final loop
		for group in group_order:
			# parse each group's content
			group_data = groups[group]
			ipa_transcriptions = {}
			nonphone_group = {}
			nonphones = {}
			for phoneset in phonesets:
				if group_data[phoneset]:
					data = group_data[phoneset].split(' ')
					assert len(data) % 2 == 0, \
						"Invalid structure phoneset: {0}, group: {1}, number of items should be even".format(phoneset, group)
					nonphone_group[phoneset] = False
				else:
					data = []
				ipa_transcriptions[phoneset] = {}
				nonphones[phoneset] = [] 
				for i in range(len(data)//2):
					symbol = data[2*i]
					ipa = data[2*i+1]
					assert not(ipa in ipa_transcriptions[phoneset]), \
						u"Invalid structure phoneset: {0}, group: {1}, two different symbols have the same IPA transcription {2}".format(phoneset, group, ipa)
					if not(ipa == u'#'):
						ipa_transcriptions[phoneset][ipa] = symbol
					else:
						nonphone_group[phoneset] = True
						nonphones[phoneset].append(symbol)
						# special symbols with no ipa transcription are just dropped from the table for now
				if phoneset != 'examples':  # a same example word can illustrate several phones
					symbols = ipa_transcriptions[phoneset].values()
					symbol_set = set(symbols)
					assert len(symbols) == len(symbol_set), \
						"Invalid structure phoneset: {0}, group: {1}, the same symbol is used with two different IPA transcription".format(phoneset, group)
			# make sure silence/noise markers are not mixed with regular phones
			if any(nonphone_group.values()):
				assert all(nonphone_group.values()), \
					u"Invalid structure, group: {0}, phonesets: {1}, silence/noise markers are mixed with regular phones".format(group, phonesets)
				# print nonphone table (no fusing of symbols across phonesets)
				# header
				# no examples for silence/noise markers	
				nb_cols = len(phonesets)-1 if u'examples' in phonesets else len(phonesets)				
				out.write(u'^  __//{0}//__  {1}\n'.format(group, u'^'*nb_cols))  # title
				for phoneset in phonesets:
					if phoneset != u'examples':
						out.write(u'^'+ phoneset) 
				out.write(u'^\n')
				# body
				ind = 0
				for phoneset in phonesets:
					if phoneset != u'examples':
						for symbol in nonphones[phoneset]:
							out.write(u'|  ')
							for i in range(ind):
								out.write(u'|  ')
							out.write(u'<nowiki> ' + symbol + u' </nowiki>') 
							for i in range(nb_cols-ind-1):
								out.write(u'  |')
							out.write(u'  |')
							out.write(u'\n')
						ind = ind+1
				out.write(u'\n')
			else:	
				# fuse IPA symbols across phonesets for each group
				all_ipas = set()
				dictionary = {}
				for phoneset in phonesets:
					all_ipas = set.union(all_ipas, ipa_transcriptions[phoneset].keys())
				for ipa in all_ipas:
					dictionary[ipa] = {} 
					for phoneset in phonesets:
						try:
							dictionary[ipa][phoneset] = ipa_transcriptions[phoneset][ipa]
						except KeyError:
							 dictionary[ipa][phoneset] = u''
				# do not display empty tables
				if dictionary:
					# generate a table in dokuwiki format 
					# using <nowiki></nowiki> tags to print special characters verbatim			
					out.write(u'^  __//{0}//__  {1}\n'.format(group, u'^'*(len(phonesets)+1)))  # title
					# column headings
					# we don't use the tags for the headings 
					# since we don't expect specials characters there
					examples = False
					for phoneset in phonesets:
						if phoneset == u'examples':
							examples = True
						else:
							out.write(u'^'+ phoneset) 
					out.write(u'^IPA^')
					if examples:
						out.write(u'examples^')
					out.write(u'\n')
					# line by line content
					# lexicographic sorted for want of something better
					items = dictionary.items()
					lines = [(e, [f[phoneset] for phoneset in phonesets]) for e, f in items]					
					sorted_lines = sorted(lines, key=operator.itemgetter(1))
					for ipa, _ in sorted_lines:
						out.write(u'|  ')
						for phoneset in phonesets:
							if phoneset != u'examples':
								out.write(u'<nowiki> ' + dictionary[ipa][phoneset] + u' </nowiki>  |  ')
						out.write(u'<nowiki> ' + ipa + u' </nowiki>  |')
						if examples:
							out.write(u'  <nowiki> ' + dictionary[ipa]['examples'] + u' </nowiki>  |')
						out.write(u'\n')
					out.write(u'\n')
		

def load_phoneset(phoneset_file):
	# read file	
	with codecs.open(phoneset_file, mode='r', encoding='utf_8') as inp:
		lines = inp.readlines()
		assert len(lines) % 2 == 0, \
			"Invalid structure file {0}: number of lines should be even".format(phoneset_file)
	# parse content into groups
	raw_groups = {}
	for i in range(len(lines)//2):
		group = lines[2*i][:-1]   # remove newline characters
		assert not(group in raw_groups), \
			u"Invalid structure file {0}: two groups have the same name".format(phoneset_file)
		raw_groups[group] = lines[2*i+1][:-1]  # remove newline characters	
	# parse each group
	groups = {}
	silence_groups = []
	for group in raw_groups:
		group_data = raw_groups[group]
		ipa_transcriptions = {}
		silences = []			
		if group_data:
			data = group_data.split(' ')
			assert len(data) % 2 == 0, \
				u"Invalid structure file: {0}, group: {1}, number of items should be even".format(phoneset_file, group)
		else:
			data = []
		ipa_transcriptions = {}
		for i in range(len(data)//2):
			symbol = data[2*i]
			ipa = data[2*i+1]
			assert not(ipa in ipa_transcriptions), \
				u"Invalid structure file: {0}, group: {1}, two different symbols have the same IPA transcription {2}".format(phoneset_file, group, ipa)
			if not(ipa == u'#'):
				ipa_transcriptions[ipa] = symbol
			else:
				silences.append(symbol)
		if silences:
			assert len(silences) == len(data)//2, \
				u"Invalid structure file: {0}, group: {1}, silence/noise markers are mixed with regular phones".format(phoneset_file, group)
			groups[group] = silences
			silence_groups.append(group)
		else:
			groups[group] = ipa_transcriptions
	phone_groups = [e for e in groups if not(e in silence_groups)]
	assert not('silences' in phone_groups), \
			"Invalid structure file {0}: group called 'silences' contains regular phones".format(phoneset_file)
	
	return groups, silence_groups, phone_groups
								
 
def export_phoneset(phoneset_file, output_folder,
			     phones=None, variants=None, verbose=0):
	"""
	Convert a phoneset file to a set of files directly usable in a kaldi recipe
	and for standard ABX analyses
	See:
		http://cogito.ens.fr/dokuwiki/doku.php?id=science:teams:models:abkhazia:abx-kaldi-standard-analyses
	"""
	groups, silence_groups, phone_groups = load_phoneset(phoneset_file)
	phone_symbols = [groups[g][ipa] for g in phone_groups for ipa in groups[g]] 
	ipas = [ipa for g in phone_groups for ipa in groups[g]]
	silence_symbols = [s for g in silence_groups for s in groups[g]]
	# check consistency of symbols
	p_set = set(phone_symbols)
	ipa_set = set(ipas)
	s_set = set(silence_symbols)
	assert len(p_set)==len(phone_symbols), \
		"Invalid structure file {0}: some phone symbols are used more than once".format(phoneset_file)
	assert len(s_set)==len(silence_symbols), \
		"Invalid structure file {0}: some silence symbols are used more than once".format(phoneset_file)
	assert len(ipa_set)==len(ipas), \
		"Invalid structure file {0}: different phone symbols have the same IPA transcription".format(phoneset_file)
	I_ps = set.intersection(p_set, s_set)
	assert not(I_ps), \
		"Invalid structure file {0}: symbol {1} is used to describe both a phone and a silence".format(phoneset_file, I_ps.pop())
	# prepare silences
	if len(silence_groups) > 1:
		if verbose > 0:
			print("[info] export_phoneset: several silence groups in file {0}, they will be merged".format(phoneset_file))
		# merge silence groups
		for g in silence_groups:
			del groups[g]
		groups['silences'] = silence_symbols
	elif len(silence_groups) == 1 and silence_groups[0] != 'silences':
		groups['silences'] = groups[silence_groups[0]]
		del groups[silence_groups[0]]
	# deal with phones and variants arguments
	if phones is None:
		main_phone_groups = phone_groups
	else:
		for p in phones:
			if not(p in phone_groups):
				raise ValueError('No such group {0} in file {1}'.format(p, phoneset_file))
		main_phone_groups = phones
	
	if variants is None:
		variants = []
	else:
		for g, v in variants:
			if not(g in phone_groups):
				raise ValueError('No such phone group {0} in file {1}'.format(g, phoneset_file))	
			if not(v in phone_groups):
				raise ValueError('No such phone group {0} in file {1}'.format(v, phoneset_file))
			# do not allow variant groups to be in main_phone_groups
			if g in main_phone_groups:
				if verbose > 0:
					print("group {0} used to generate variants, removing it from main groups".format(g))
				del(main_phone_groups[g])
			if v in main_phone_groups:
				if verbose > 0:
					print("group {0} used to generate variants, removing it from main groups".format(v))
				del(main_phone_groups[v])				
	variated_groups = [g for g, _ in variants]
	assert len(set(variated_groups))==len(variated_groups), \
		"More than one variant by group not supported"
	# create list of variants
	phone_variants = {}			
	for g, v in variants:
		for ipa1 in groups[g]:
			phone_variants[ipa1] = {}
			symbol1 = groups[g][ipa1]
			for ipa2 in groups[v]:  
				symbol2 = groups[v][ipa2] 
				phone_variants[ipa1][ipa1 + ipa2] = symbol1 + symbol2
	# create list of phones
	phones = {}
	for g in groups:
		if g in phone_groups:
			if g in variated_groups:
				for ipa in groups[g]:
					for ipa_v in phone_variants[ipa]:
						phones[phone_variants[ipa][ipa_v]] = ipa_v
			elif g in main_phone_groups:
				for ipa in groups[g]:
					phones[groups[g][ipa]] = ipa
	ordered_symbols = phones.keys()
	ordered_symbols.sort() 
	# list of silences is already ready
	if 'silences' in groups:
		silences = groups['silences']
	else:
		silences = []
	silences.sort()
	# check unicity of symbols and ipa transcriptions
	all_symbols = phones.keys() + silences
	all_ipas = phones.values()
	assert len(set(all_symbols))==len(all_symbols), \
		"Some symbols end up being used twice"
	assert len(set(all_ipas))==len(all_ipas), \
		"Some IPA transcriptions are used with two different symbols"		
	#print outputs phones.txt, silences.txt, extra_questions.txt
	p_file = os.path.join(output_folder, 'phones.txt')
	s_file = os.path.join(output_folder, 'silences.txt')
	e_file = os.path.join(output_folder, 'extra_questions.txt')
	if not(os.path.isdir(output_folder)):
		if verbose>0:
			print("Directory {0} doesn't exist, creating it".format(output_folder))
		os.mkdir(output_folder)
	with codecs.open(p_file, mode='w', encoding='UTF-8') as out:
		for symbol in ordered_symbols:
			out.write(u'{0} {1}\n'.format(symbol, phones[symbol]))
	with codecs.open(s_file, mode='w', encoding='UTF-8') as out:
		for symbol in silences:
			out.write(u'{0}\n'.format(symbol))
	with codecs.open(e_file, mode='w', encoding='UTF-8') as out:
		for ipa in phone_variants:
			ipas = [ipa_v for ipa_v in phone_variants[ipa]]
			out.write(u' '.join(ipas) + u'\n')
			

if __name__ == '__main__':
	# create phonesets files
	root = '../phonesets'
	AI = os.path.join(root, 'AI.txt')
	Buckeye = os.path.join(root, 'Buckeye.txt')
	CMU = os.path.join(root, 'CMU.txt')
	TIMIT61 = os.path.join(root, 'TIMIT-61.txt')
	AM_EN_examples = os.path.join(root, 'AM-EN-examples.txt')
	
	GP_Mandarin = os.path.join(root, 'GP_Mandarin.txt')
	GP_Vietnamese = os.path.join(root, 'GP_Vietnamese.txt')
	
	root = '../phoneset_tables'
	if not(os.path.isdir(root)):
		os.mkdir(root)
	phonesets2table(os.path.join(root, 'AmericanEnglish.txt'), [TIMIT61, Buckeye, CMU, AI, AM_EN_examples],
			      phonesets=['TIMIT-61', 'Buckeye', 'CMU', 'AI', 'examples'],
				 group_order=['phones', 'silences'])
	phonesets2table(os.path.join(root, 'Mandarin.txt'), [GP_Mandarin],
				 phonesets=['GlobalPhone Mandarin'],
				 group_order=['consonants', 'vowels',
					'tones', 'silences'])
	phonesets2table(os.path.join(root, 'Vietnamese.txt'), [GP_Vietnamese],
				 phonesets=['GlobalPhone Vietnamese'],
				 group_order=['consonants', 'vowels', 'tones'])
					
	root = '../standardized_phonesets'
	export_phoneset(AI, os.path.join(root, 'AI'), verbose=1)
	export_phoneset(Buckeye, os.path.join(root, 'Buckeye'), verbose=1)
	export_phoneset(CMU, os.path.join(root, 'CMU'), verbose=1)
	export_phoneset(TIMIT61, os.path.join(root, 'TIMIT_61'), verbose=1)
	export_phoneset(GP_Mandarin, os.path.join(root, 'GP_Mandarin'), 
				  phones=['consonants'], variants=[('vowels', 'tones')],
				  verbose=1)
	export_phoneset(GP_Vietnamese, os.path.join(root, 'GP_Vietnamese'), 
				  phones=['consonants'], variants=[('vowels', 'tones')],													
				  verbose=1)
	
	