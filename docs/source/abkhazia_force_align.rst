================
Forced Alignment
================

This tutorial covers the usage of abkhazia to do phone-level forced alignment
on your own corpus of annotated audio files.

Prerequisites
=============
Here's what you need to have before being able to follow this tutorial:

- A set of audio files encoded in 16000kz WAV 16bit PCM on which to run the alignment
- On these audio files, a set of segments corresponding to utterances. For each utterance, you'll
  need to have a phonemic transcription (an easy way to get these is by
  using [Phonemizer](https://github.com/bootphon/phonemizer) )

It's also recommended (yet optional) to have some kind of reference file where you can identify
the speaker of each of your phonemized utterance.

Corpus format
=============

The corpus format is the same as the one specified in :ref:`abkhazia_format`, two
 corpus files having a bit more specific format, namely ``text.txt`` and ``lexicon.txt``.
 Here, ``text.txt`` is composed of your phonemic transcription of each utterance::

  <utterance-id> <pho1> <pho2> ... <phoN>


and ``lexicon.txt`` is just a "phony" file containg phonemes mapped to themselves::

  <pho1> <pho1>
  <pho2> <pho2>
  <pho3> <pho3>
  ...


Doing the Forced Alignment
==========================

Once you've gathered all the required files (cited above) in a ``corpus/`` folder (the name is
obviously arbitrary), you'll want to validate the corpus to check that it is conform to Kaldi's
input format. Abkhazia luckily does that for us::

  abhkazia validate corpus/


Then, we'll compute the language model (actually here a phonetic model) for your dataset.
Note that even though we set the model-level (option ``-l``) to "word", here it's
still working find since all words are phonemes::

  abkhazia language corpus/ -l word -n 3 -v


We'll now extract the MFCC features from the wav files::

  abkhazia features mfcc corpus/ --cmvn


Then, using the langage model and the extracted MFCC's, compute a triphone HMM-GMM acoustic model::

  abkhazia acoustic monophone -v corpus/ --force --recipe
  abkhazia acoustic triphone -v corpus/

If you specified the speaker for each utterance, you can adapt your model per speaker::

  abkhazia acoustic triphone-sa -v corpus/

And the, at last, we can compute the forced phonetic aligments::

  abkhazia align corpus -a corpus/triphone-sa # if you computed the speaker-adapted triphones
  abkhazia align corpus -a corpus/triphone # if you didn't


If everything went right, you should be able to find your alignment in
``corpus/align/alignments.txt``. The file will have the following row structure::

  <utt_id> <pho_start> <pho_end> <pho_name> <pho_symbol>
  ...

**Note that the phoneme's start and end time markers (in seconds) are relative to the utterance
in which they were contained, not to the entire audio file.**