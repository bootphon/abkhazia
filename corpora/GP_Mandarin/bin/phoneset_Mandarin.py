# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:17:47 2015

@author: Thomas Schatz
"""


# Main sources:
#	http://talkbank.org/pinyin/Trad_chart_IPA.php
# 	http://en.wikipedia.org/wiki/Pinyin#Overview
# See also:
#	http://ling.cass.cn/yuyin/english/sampac/sampac.htm
# 	http://en.wikipedia.org/wiki/Standard_Chinese_phonology#Palatal_series
# GP_Mandarin includes the palatal series in its phoneset, but
# the glide series is integrated into the vowels

vowels = [
	('a', u'ä'),
	('e', u'ə'),
	('i', u'i'),
	('ii', u'ɨ'),
	('o', u'ɤ'),
	('u', u'u'),
	('v', u'y'),
	('ai', u'aɪ'),
	('ao', u'ɑʊ'),
	('ei', u'eɪ'),
	('ia', u'iä'),
	('ie', u'iɛ'),
	('io', u'iʊ'),
	('iu', u'iu'), # according to the sources above, 'iu' should be completely folded with 'iou'...
	('ou', u'oʊ'),
	('ua', u'uä'),
	('ue', u'uə'), # here the two sources above disagree with GP who proposes 'uɛ' I think
	('uo', u'uɔ'), # discrepancy here too... (but not sure what GP proposition is due to font issues in pdf)
	('iao', u'iɑʊ'),
	('uai', u'uaɪ'),
	('uei', u'ueɪ'), # here too GP proposes 'uɛi' I think
	('va', u'yɛ'), # 4 tone vowel: never happens with tone 5
	('ve', u'yœ'), # 4 tone vowel: never happens with tone 5
	('iou', u'ioʊ') # here GP proposes iʊu; 4 tone vowel: never happens with tone 5 
]

# no glides (j, w and ɥ) in the GP version (they are in the vowels)
# meaning that many of the diphtongs and triphtongs
# could have an alternative translation with a glide
# at the beginning as in 
# http://talkbank.org/pinyin/Trad_chart_IPA.php
consonants = [
	('b', u'p'),
	('c', u'tsʰ'),
	('ch', u'tʂʰ'),
	('d', u't'),
	('f', u'f'),
	('g', u'k'),
	('h', u'x'),
	('j', u'tɕ'),
	('k', u'kʰ'),
	('l', u'l'),
	('m', u'm'),
	('n', u'n'),
	('ng', u'ŋ'),
	('p', u'pʰ'),
	('q', u'tɕʰ'),
	('r', u'ɻ'),
	# a common alternative is ʐ, the only difference is in the manner of articulation:
	# ʐ is a sibilant fricative 
	# ɻ is an approximant
	('s', u's'),
	('sh', u'ʂ'),
	('t', u'tʰ'),
	('x', u'ɕ'),
	('z', u'ts'),
	('zh', u'tʂ')
]

# source for IPA notation: https://en.wikipedia.org/wiki/Tone_%28linguistics%29#Phonetic_notation
tones = [
	('1', u'˥'),
	('2', u'˧˥'),
	('3', u'˨˩˦'),
	('4', u'˥˩'),
	('5', u'˧') # mid-level (neutral)
]

four_tones_vowels = ['va', 've', 'iou']

# generate dict associating phones with ipa, silences list and tonal variants lists:
phones = {}
silences = []
variants = []

for s, ipa in consonants:
	assert not(s in phones)
	phones[s] = ipa
for s, ipa in vowels:
	if s in four_tones_vowels:
		l_tones = tones[:-1]
	else:
		l_tones = tones
	for s_t, ipa_t in l_tones:
		assert not(s+s_t in phones)
		phones[s+s_t] = ipa+ipa_t
	variants.append([s+s_t for s_t, _ in l_tones])


#TODO articulatory features, closest UPSID match and stats
