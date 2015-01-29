# -*- coding: utf-8 -*-
"""
Created on Tue Jan 20 03:43:20 2015

@author: Thomas Schatz
"""

# IPA transcription for various labeling scheme


# function to write phonesets in dedicated text file format
import codecs

def phoneset2txt(phoneset, filename):
	with codecs.open(filename, mode='w', encoding='utf-8') as f:
		for part in phoneset:
			f.write(part + u'\n')
			l = phoneset[part]
			if len(l[0]) == 2: # symbol + IPA transcript
				string = u' '.join([u' '.join(e) for e in l])
			else:
				# for special symbols (such as silences) with no IPA transcription,
				# '#' is used as a separator, since it is a simple ASCII character that
				# is not part of IPA.
				string = u' '.join([e + u' #' for e in l])
			f.write(string + u'\n')


#TODO:
# 	CSJ, NCHLT, Glissando Catalan and Spanish, Blue lips
#	For CSJ at least need to do some ABX experiment to decide appropriate
#	labeling scheme. 


## English ##
# General American phonology according to wikipedia

# AI and CMU map exactly the same phone sets (the xh from AI is
# actually never used in the corpus), it's also the same set as the
# TIMIT39 
# Buckeye has 7 more consonants: 
#	syllabic l, m, n, two flaps, a variant of ng and glottal stop
#TODO: is Buckeye close from TIMIT48? 
# What about WSJ?

example_phones = [
	('beet', u'iː'),
	('bit', u'ɪ'),
	('bet', u'ɛ'),
	('bait', u'eɪ'),
	('bat', u'æ'),
	('bott', u'ɑː'),
	('bout', u'aʊ'),
	('bite', u'aɪ'),
	('but', u'ʌ'),
	('bought', u'ɔː'),
	('boy', u'ɔɪ'),
	('boat', u'oʊ'),
	('book', u'ʊ'),
	('boot', u'uː'),
	('toot', u'u\u0308ː'), # fronted-u ux, allophone of uw, typically found in alveolar context
	('bird', u'ɝ'),
	('about', u'ə'),
	('debit', u'ɨ'),
	('butter', u'ɚ'),
	('suspect', u'ə\u0325'), 
	# devoied shcwa: very short, devoiced vowel, typically occurring
	# for reduced vowels surrounded by voiceless consonants
	('joke', u'ʤ'),
	('choke', u'ʧ'),
	('bee', u'b'),
	('day', u'd'),
	('gay', u'g'),
	('pea', u'p'),
	('tea', u't'),
	('key', u'k'),
	('muddy', u'ɾ'), # flap, such as in words "muddy" or "dirty"
	('sea', u's'),
	('she', u'ʃ'),
	('zone', u'z'),
	('azure', u'ʒ'),
	('fin', u'f'),
	('thin', u'θ'),
	('van', u'v'),
	('then', u'ð'),
	('mom', u'm'),
	('noon', u'n'),
	('sing', u'ŋ'),
	('bottom', u'm\u0329'),
	('winner', u'ɾ\u0303'), # nasal flap, as in "winner"
	('button', u'n\u0329'),
	('washington', u'ŋ\u0329'),
	('lay', u'l'),
	('ray', u'r'),
	('way', u'w'),
	('yacht', u'j'),
	('hay', u'h'),
	('ahead', u'ʍ'), # voiced-h, a voiced allophone of h, typically found intervocalically
	('bottle', u'l\u0329'),
	('bat', u'ʔ') 
]

examples = {
	'phones': example_phones
}

AI_phones = [
	('i', u'iː'),
	('xi', u'ɪ'),
	('xe', u'ɛ'),
	('e', u'eɪ'),
	('xq', u'æ'),
	('a', u'ɑː'),
	('xw', u'aʊ'),
	('xy', u'aɪ'),
	('xa', u'ʌ'),
	('c', u'ɔː'),
	('xo', u'ɔɪ'),
	('o', u'oʊ'),
	('xu', u'ʊ'),
	('u', u'uː'),
	('xr', u'ɝ'),
	('xj', u'ʤ'),
	('xc', u'ʧ'),
	('b', u'b'),
	('d', u'd'),
	('g', u'g'),
	('p', u'p'),
	('t', u't'),
	('k', u'k'),
	('s', u's'),
	('xs', u'ʃ'),
	('z', u'z'),
	('xz', u'ʒ'),
	('f', u'f'),
	('xt', u'θ'),
	('v', u'v'),
	('xd', u'ð'),
	('m', u'm'),
	('n', u'n'),
	('xg', u'ŋ'),
	('l', u'l'),
	('r', u'r'),
	('w', u'w'),
	('y', u'j'),
	('h', u'h')
]
AI_silences = ['sil'] # get rid of spn
AI_optional_silence = ['sil']

AI = {
	'phones': AI_phones,
	'silences': AI_silences,
	'optional silence': AI_optional_silence
}


CMU_phones = [
	('IY', u'iː'),
	('IH', u'ɪ'),
	('EH', u'ɛ'),
	('EY', u'eɪ'),
	('AE', u'æ'),
	('AA', u'ɑː'),
	('AW', u'aʊ'),
	('AY', u'aɪ'),
	('AH', u'ʌ'),
	('AO', u'ɔː'),
	('OY', u'ɔɪ'),
	('OW', u'oʊ'),
	('UH', u'ʊ'),
	('UW', u'uː'),
	('ER', u'ɝ'),
	('JH', u'ʤ'),
	('CH', u'ʧ'),
	('B', u'b'),
	('D', u'd'),
	('G', u'g'),
	('P', u'p'),
	('T', u't'),
	('K', u'k'),
	('S', u's'),
	('SH', u'ʃ'),
	('Z', u'z'),
	('ZH', u'ʒ'),
	('F', u'f'),
	('TH', u'θ'),
	('V', u'v'),
	('DH', u'ð'),
	('M', u'm'),
	('N', u'n'),
	('NG', u'ŋ'),
	('L', u'l'),
	('R', u'r'),
	('W', u'w'),
	('Y', u'j'),
	('HH', u'h')
]
# silences? (at least in WSJ)
CMU = {
	'phones': CMU_phones,
}


Buckeye_phones = [
	('iy', u'iː'),
	('ih', u'ɪ'),
	('eh', u'ɛ'),
	('ey', u'eɪ'),
	('ae', u'æ'),
	('aa', u'ɑː'),
	('aw', u'aʊ'),
	('ay', u'aɪ'),
	('ah', u'ʌ'),
	('ao', u'ɔː'),
	('oy', u'ɔɪ'),
	('ow', u'oʊ'),
	('uh', u'ʊ'),
	('uw', u'uː'),
	('er', u'ɝ'),
	('jh', u'ʤ'),
	('ch', u'ʧ'),
	('b', u'b'),
	('d', u'd'),
	('g', u'g'),
	('p', u'p'),
	('t', u't'),
	('k', u'k'),
	('dx', u'ɾ'),
	('s', u's'),
	('sh', u'ʃ'),
	('z', u'z'),
	('zh', u'ʒ'),
	('f', u'f'),
	('th', u'θ'),
	('v', u'v'),
	('dh', u'ð'),
	('m', u'm'),
	('n', u'n'),
	('ng', u'ŋ'),
	('em', u'm\u0329'),
	('nx', u'ɾ\u0303'),
	('en', u'n\u0329'),
	('eng', u'ŋ\u0329'),
	('l', u'l'),
	('r', u'r'),
	('w', u'w'),
	('y', u'j'),
	('hh', u'h'),
	('el', u'l\u0329'),
	('tq', u'ʔ')
]
# silences ?
Buckeye = {
	'phones': Buckeye_phones,
}


# source: https://catalog.ldc.upenn.edu/docs/LDC93S1/PHONCODE.TXT
TIMIT61_phones = [
	('iy', u'iː'),
	('ih', u'ɪ'),
	('eh', u'ɛ'),
	('ey', u'eɪ'),
	('ae', u'æ'),
	('aa', u'ɑː'),
	('aw', u'aʊ'),
	('ay', u'aɪ'),
	('ah', u'ʌ'),
	('ao', u'ɔː'),
	('oy', u'ɔɪ'),
	('ow', u'oʊ'),
	('uh', u'ʊ'),
	('uw', u'uː'),
	('ux', u'u\u0308ː'), # fronted-u ux, allophone of uw, typically found in alveolar context
	('er', u'ɝ'),
	('ax', u'ə'),
	('ix', u'ɨ'),
	('axr', u'ɚ'),
	('ax-h', u'ə\u0325'), 
	# devoied shcwa: very short, devoiced vowel, typically occurring
	# for reduced vowels surrounded by voiceless consonants
	('jh', u'ʤ'),
	('ch', u'ʧ'),
	('b', u'b'),
	('d', u'd'),
	('g', u'g'),
	('p', u'p'),
	('t', u't'),
	('k', u'k'),
	('dx', u'ɾ'), # flap, such as in words "muddy" or "dirty"
	('s', u's'),
	('sh', u'ʃ'),
	('z', u'z'),
	('zh', u'ʒ'),
	('f', u'f'),
	('th', u'θ'),
	('v', u'v'),
	('dh', u'ð'),
	('m', u'm'),
	('n', u'n'),
	('ng', u'ŋ'),
	('em', u'm\u0329'),
	('nx', u'ɾ\u0303'), # nasal flap, as in "winner"
	('en', u'n\u0329'),
	('eng', u'ŋ\u0329'),
	('l', u'l'),
	('r', u'r'),
	('w', u'w'),
	('y', u'j'),
	('hh', u'h'),
	('hv', u'ʍ'), # voiced-h, a voiced allophone of h, typically found intervocalically
	('el', u'l\u0329'),
	('q', u'ʔ') 
	# glottal stop, which may be an allophone of t, or may mark an initial 
     # vowel or a vowel-vowel boundary
]
TIMIT61_silences = ['pau', 'epi', 'h#', 
				 'bcl', 'dcl', 'gcl', 'pcl', 'tcl', 'kcl']					
# pause, epenthetic silence, begin/end marker, closures (i.e. silences)
# optional silence: according to the kaldi recipe:
# 	in TIMIT the silence appears also as a word in the dictionary and is scored
# anyway the custom recipe should probably be used for this one rather than
# a standard one ?
TIMIT61 = {
	'phones': TIMIT61_phones,
	'silences': TIMIT61_silences
}


TIMIT48_subst = [
	('ax-h', 'ax'),
	('axr', 'er'),
	('hv', 'hh'),
	('em', 'm'),
	('nx', 'n'),
	('eng', 'ng'),
	('ux', 'uw'),
]
TIMIT48_dropped = ['q']
TIMIT48_specials =  [
	('pau', 'sil'),
	('h#', 'sil'), 
	('bcl', 'vcl'),
	('dcl', 'vcl'),
	('gcl', 'vcl'),
	('pcl', 'cl'),
	('tcl', 'cl'),
	('kcl', 'cl')
]


TIMIT39_subst = [
	('ao', 'aa'),
	('ax', 'ah'),
	('ax-h', 'ah'),
	('axr', 'er'),
	('hv', 'hh'),
	('ix', 'ih'),
	('el', 'l'),
	('em', 'm'),
	('en', 'n'),
	('nx', 'n'),
	('eng', 'ng'),
	('zh', 'sh'),
	('ux', 'uw'),
]
TIMIT39_dropped = ['q']
TIMIT39_specials =  [
	('pau', 'sil'),
	('epi', 'sil'),
	('h#', 'sil'), 
	('bcl', 'sil'),
	('dcl', 'sil'),
	('gcl', 'sil'),
	('pcl', 'sil'),
	('tcl', 'sil'),
	('kcl', 'sil')
]


## Mandarin ##
# Main sources for this:
#	http://talkbank.org/pinyin/Trad_chart_IPA.php
# 	http://en.wikipedia.org/wiki/Pinyin#Overview
# See also:
#	http://ling.cass.cn/yuyin/english/sampac/sampac.htm
# 	http://en.wikipedia.org/wiki/Standard_Chinese_phonology#Palatal_series
# GP includes the palatal series in its phoneset, but
# the glide series is integrated into the vowels
GP_Mandarin_4tones_vowels = [	
	('va', u'yɛ'),
	('ve', u'yœ'),
	('iou', u'ioʊ') # here GP proposes iʊu 
]

GP_Mandarin_5tones_vowels = [
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
	('uo', u'uɔ'), # discrepancy here too... (but not sure what GP proposition is due to font issues)
	('iao', u'iɑʊ'),
	('uai', u'uaɪ'),
	('uei', u'ueɪ') # here too GP proposes 'uɛi' I think
]

# no glides (j, w and ɥ) in the GP version (they are in the vowels)
# meaning that many of the diphtongs and triphtongs
# could have an alternative translation with a glide
# at the beginning as in 
# http://talkbank.org/pinyin/Trad_chart_IPA.php
GP_Mandarin_consonants = [
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
GP_Mandarin_tones = [
	('1', u'˥'),
	('2', u'˧˥'),
	('3', u'˨˩˦'),
	('4', u'˥˩'),
	('5', u'˧') # mid-level (neutral)
]

GP_Mandarin_silences = ['+QK', '+hGH', 'sil']
# speech fragments, noise, silece respectively
GP_Mandarin_optional_silence = ['sil']

GP_Mandarin = {
	'consonants': GP_Mandarin_consonants,
	'4 tones vowels': GP_Mandarin_4tones_vowels,
	'5 tones vowels': GP_Mandarin_5tones_vowels,
	'tones': GP_Mandarin_tones,
	'silences': GP_Mandarin_silences,
	'optional silence': GP_Mandarin_optional_silence
}


## Vietnamese ##
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
GP_Vietnamese_vowels = [
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

GP_Vietnamese_consonants = [
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
GP_Vietnamese_tones = [
	('1', u'˧'), # mid-level (neutral)
	('2', u'˨˩'),
	('3', u'˧˥'),
	('4', u'˧˩˧'),
	('5', u'˧\u0330˥\u0330'), # + creaky voice
	# apparently no ipa symbol for 'ˀ' (glottalized), so used 
	# u'˧\u0330˥\u0330' instead of u'˧ˀ˥' (using the creaky voice diacritic)
	('6', u'˨\u0330˩\u0330ʔ') # + creaky voice
	# apparently no ipa symbol for 'ˀ' (glottalized), so used 
	# u'˨\u0330˩\u0330ʔ' instead of u'˨ˀ˩ʔ' (using the creaky voice diacritic)
]

GP_Vietnamese_silences = ['sil']
# any other special phone ?
GP_Vietnamese_optional_silence = ['sil']
## Xitsonga ##
# phoneset focused on phonemic rather than phonetic distinctions, according to 
# the authors of the corpus


#TODO: check which vowels are observed with which tones?
GP_Vietnamese = {
	'consonants': GP_Vietnamese_consonants,
	'vowels': GP_Vietnamese_vowels,
	'tones': GP_Vietnamese_tones,
	'silences': GP_Vietnamese_silences,
	'optional silence': GP_Vietnamese_optional_silence
}




import os
root = '../phonesets/'
if not(os.path.isdir(root)):
	os.mkdir(root)
phoneset2txt(GP_Mandarin, os.path.join(root, 'GP_Mandarin.txt'))
phoneset2txt(GP_Vietnamese, os.path.join(root, 'GP_Vietnamese.txt'))
phoneset2txt(TIMIT61, os.path.join(root, 'TIMIT-61.txt'))
phoneset2txt(Buckeye, os.path.join(root, 'Buckeye.txt'))
phoneset2txt(CMU, os.path.join(root, 'CMU.txt'))
phoneset2txt(AI, os.path.join(root, 'AI.txt'))
phoneset2txt(examples, os.path.join(root, 'AM-EN-examples.txt'))