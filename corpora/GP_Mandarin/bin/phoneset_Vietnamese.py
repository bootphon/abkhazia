# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""


# Main source:
#	GP documentation
# Other sources:
#	https://en.wikipedia.org/wiki/Vietnamese_phonology
#	https://en.wikipedia.org/wiki/Tone_%28linguistics%29#Phonetic_notation
#	http://en.wikipedia.org/wiki/Vietnamese_alphabet

# Main source for vowels only: https://en.wikipedia.org/wiki/Vietnamese_phonology
# except for ɨ/ɯ, following: http://www.academia.edu/1972509/Vietnamese_Hanoi_Vietnamese_
# Note diphtongs are often presented as vowel+glide, we followed GP
# choice of vowel+vowel
# For vowel length we have normal and extra-short (is it maybe long and short?)
vowels = [
	# a1 and a2 are exchanged in the GP handout!!! (as seen by looking into the dict)
	('a2', u'ă'), 	# short a, sometimes for both a and schwa,
				# the length contrasts are reported as /a/, /a:/
	('a1', u'a'), # both a's are sometimes reported as more centralized... 
	('a3', u'ə\u0306'), # short schwa
	('e1', u'ɛ'),
	('e2', u'e'),
	('i', u'i'),
	('o1', u'ɔ'),
	('o2', u'o'),
	('o3', u'ɤː'), # sometimes reported as a əː (long version of u'ə')
	('u1', u'u'),
	('u2', u'ɨ'), # sometimes reported as ɯ
	('ai', u'ai'),
	('ao', u'aʊ'), # why not au?
	('au', u'ăʊ'), # why not ău?
	('au3', u'ə\u0306ʊ'),
	('ay', u'ăi'),
	('ay3', u'ə\u0306i'),	
	('eo', u'ɛʊ'),
	('eu', u'eʊ'),
	('ie2', u'iə\u0306'),
	('iu', u'iʊ'),
	('oa', u'oa'), # not sure about this one, not documented in GP handout and not documented on wikipedia either...
	('oe', u'ʊə'), # reversed the proposed translation which seemed really weird
	#  here and was not documented in wikipedia + shouldn't ə be replaced by ɤ?
	('oi', u'ɔi'),
	('oi2', u'oi'),
	('oi3', u'əi'), # shouldn't ə be replaced by ɤ?
	('ua', u'uə\u0306'),
	('ua2', u'ɨə\u0306'),
	('ui', u'ui'),
	('ui2', u'ɨi'),
	('uu2', u'ɨʊ'),
	('uy', u'uːi'), # this one is not clear	
	('ieu', u'iə\u0306ʊ'),
	('uoi2', u'uə\u0306i'),
	('uoi3', u'ɨə\u0306i'),
	('uou', u'ɨə\u0306ʊ')
]

consonants = [
	('b', u'ɓ'),
	('ch', u'tɕ'), # possibly not affricate?
	('d1', u'ɟ'), 
	# this phoneme is not reported in wikipedia vietnamese phonology
	# although it is said to occur in north-central vietnamese dialect on 
	# wikipedia 'ɟ' page
	('d2', u'ɗ'),
	('g', u'ɣ'),
	('h', u'h'),
	('j', u'j'),
	('k', u'k'),
	('kh', u'x'),
	('l', u'l'),
	('m', u'm'),
	('n', u'n'),
	('ng', u'ŋ'),
	('p', u'p'),
	('ph', u'f'),
	('r', u'ʐ'),
	('s', u'ʂ'),	
	('t', u't'),
	('th', u'tʰ'),
	('tr', u'ʈ'), # possibly affricate?
	('x', u's'),
	('v', u'v')
]

# https://en.wikipedia.org/wiki/Vietnamese_phonology#Six-tone_analysis
# (northern part)
tones = [
	('_1', u'˧'), # mid-level (neutral)
	('_2', u'˨˩'),
	('_3', u'˧˥'),
	('_4', u'˧˩˧'),
	('_5', u'˧\u0330˥\u0330'), # + creaky voice
	# apparently no ipa symbol for 'ˀ' (glottalized), so used 
	# u'˧\u0330˥\u0330' instead of u'˧ˀ˥' (using the creaky voice diacritic)
	('_6', u'˨\u0330˩\u0330ʔ') # + creaky voice
	# apparently no ipa symbol for 'ˀ' (glottalized), so used 
	# u'˨\u0330˩\u0330ʔ' instead of u'˨ˀ˩ʔ' (using the creaky voice diacritic)
]

# generate dict associating phones with ipa, silences list and tonal variants lists:
phones = {}
silences = []
variants = []

for s, ipa in consonants:
	assert not(s in phones)
	phones[s] = ipa
for s, ipa in vowels:
	for s_t, ipa_t in tones:
		assert not(s+s_t in phones)
		phones[s+s_t] = ipa+ipa_t
	variants.append([s+s_t for s_t, _ in tones])


#TODO: check which vowels are observed with which tones?

#TODO articulatory features, closest UPSID match and stats

