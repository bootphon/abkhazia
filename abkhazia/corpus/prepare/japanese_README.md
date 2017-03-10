Japanese Corpora
===============

Please note that the japanese corpora preparator (CSJ & globalphone) 
are WIP. For now, they need a file named "kana-to-phon_bootphon.txt"
in their input folders ( /input_folder/kana-to-phon_bootphon.txt).

** GlobalPhone
Since not all phones used in the GlobalPhone romanized transcription
are in kana-to-phon_bootphon.txt, the preparator exports a list of 
all the unknown phones in :
	/input_folder/unknown_GP.txt

** CSJ
Note that, out of 498 379 utterances, there are 58 845 utterances
that contain at least one transcription ambiguity ( notated as 
"(W ... ; ...)" ), and there are 54 484 utterances that contain
an ambiguous symbol (such as "?" which means the person who 
transcribed the utterance was not sure). For now, we keep the 
utterance and replace the whole word by "SPN" (spoken noise)

**TODO
A list (probably non-exhaustive) of things to do can be found in 
TODO.org, I will do them as quickly as possible...

 
