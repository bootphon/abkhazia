# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 14:20:27 2015

@author: Thomas Schatz
"""

#TODO:
# 	document in particular: special treatment of examples, #, ignoring specials,
#		special groups for kaldi part, 
# 	create a new phonesets code repo on github with these files
# 	xsampa compatibility check
# 	write phoneset2kaldi

# Possible improvements: 
# 	display order: sort based on articulatory features when possible
#	find a nice way to display special symbols

import codecs
import os
import operator


def phonesets2table(output_file, phonesets_files, phonesets=None, group_order=None):
	"""
	Create a nice dokuwiki table given one or several phonesets for a given language
	where phoneset files are in the format defined at:
		http://cogito.ens.fr/dokuwiki/doku.php?id=science:teams:models:abx-kaldi-standard-analyses&#phone_inventory
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
			for phoneset in phonesets:
				if group_data[phoneset]:
					data = group_data[phoneset].split(' ')
					assert len(data) % 2 == 0, \
						"Invalid structure file {0}, group {1}: number of items should be even".format(phoneset_file, group)				
				else:
					data = []
				ipa_transcriptions[phoneset] = {}
				dropped = []
				for i in range(len(data)//2):
					symbol = data[2*i]
					ipa = data[2*i+1]
					assert not(ipa in ipa_transcriptions[phoneset]), \
						u"Invalid structure file {0}, group {1}: two different symbols have the same IPA transcription {2}".format(phoneset_file, group, ipa)
					if not(ipa == u'#'):
						ipa_transcriptions[phoneset][ipa] = symbol
					else:
						dropped.append(symbol)
						# special symbols with no ipa transcription are just dropped from the table for now
				if phoneset != 'examples':  # a same example word can illustrate several phones
					symbols = ipa_transcriptions[phoneset].values()
					symbol_set = set(symbols)
					assert len(symbols) == len(symbol_set), \
						"Invalid structure file {0}, group {1}: the same symbol is used with two different IPA transcription".format(phoneset_file, group)
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
							out.write(u'<nowiki>' + dictionary[ipa][phoneset] + u' </nowiki>  |  ')
					out.write(u'<nowiki>' + ipa + u' </nowiki>  |')
					if examples:
						out.write(u'  <nowiki>' + dictionary[ipa]['examples'] + u' </nowiki>  |')
					out.write(u'\n')
				out.write(u'\n')
		


def phoneset2kaldi(phoneset_file, kaldi_dict_folder, encoding='ASCII'):
	"""
	Convert a phoneset file to a set of files directly usable in a kaldi recipe
	where the phoneset file is in the format defined at:
		http://cogito.ens.fr/dokuwiki/doku.php?id=science:teams:models:abx-kaldi-standard-analyses&#phone_inventory
	"""
	assert encoding in ['ASCII', 'UTF-8'], 'Unknown encoding format {0}'.format(encoding)


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
phonesets2table(os.path.join(root, 'English.txt'), [TIMIT61, Buckeye, CMU, AI, AM_EN_examples],
		      phonesets=['TIMIT-61', 'Buckeye', 'CMU', 'AI', 'examples'])
phonesets2table(os.path.join(root, 'Mandarin.txt'), [GP_Mandarin],
			 phonesets=['GlobalPhone Mandarin'],
			 group_order=['consonants', '4 tones vowels', '5 tones vowels',
				'tones', 'silences', 'optional silence'])
phonesets2table(os.path.join(root, 'Vietnamese.txt'), [GP_Vietnamese],
			 phonesets=['GlobalPhone Vietnamese'],
			 group_order=['consonants', 'vowels', 'tones',
				         'silences', 'optional silence'])