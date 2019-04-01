================
Forced Alignment
================

This tutorial covers the usage of abkhazia to do phone-level forced alignment
on your own corpus of annotated audio files.

Prerequisites
=============
Here's what you need to have before being able to follow this tutorial:

- A set of audio files encoded in 16000kz WAV 16bit PCM on which to run the alignment
- On these audio files, a set of segments corresponding to utterance. For each utterance, you'll
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

# TODO