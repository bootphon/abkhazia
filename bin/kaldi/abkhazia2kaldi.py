# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:32:55 2015

@author: Thomas Schatz
"""

"""
This script converts a corpus in abkhazia format to standard kaldi format

Differences: different filenames

lexicon.txt: ok?
nonsilence_phones.txt: get rid of IPA
silence_phones.txt: ok
optional_silence.txt -> SIL
extra_questions.txt: ok
text ok
utt2spk ok
wav.scp and segments: a bit different

Language model?
"""