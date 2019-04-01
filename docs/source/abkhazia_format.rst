=============
Speech corpus
=============

Format definition
=================

A standardized corpus is stored as a directory composed of the
following:

- ``wavs``: subfolder containing the speech recordings in wav, either
  as files or symbolic links

- ``segments.txt``: list of utterances with a description of their
  location in the wavefiles

- ``utt2spk.txt``: list containing the speaker associated to each utterance

- ``text.txt``: transcription of each utterance in word units

- ``phones.txt``: phone inventory mapped to IPA

- ``lexicon.txt``: phonetic dictionary using that inventory

- ``silences.txt``: list of silence symbols


Supported corpora
=================

Supported corpora are (see also ``abkhazia prepare --help``:

* Articulation Index Corpus LSCP

* Buckeye Corpus of conversational speech

* Child Language Data Exchange System (only Brent part for now)

* Corpus of Interactional Data

* Corpus of Spontaneous Japanese

* GlobalPhone multilingual read speech corpus (Vietnamese and Mandarin)

* LibriSpeech ASR Corpus

* Wall Street Journal ASR Corpus

* NCHLT Xitsonga Speech Corpus


Once you have the raw data, you can import any of the above corpora in
the standardized Abkhazia format using the ``abkhazia prepare``
command, for exemple::

  abkhazia prepare csj /path/to/raw/csj -o ./prepared_csj --verbose


Note that many corpora do not form a homogeneous whole, but are
constituted from several homogenous subparts. For example in the core
subset of the [CSJ](http://www.ninjal.ac.jp/english/products/csj/)
corpus, spontaneous presentations from academics (files whos names
starts with an 'A'), spontaneous presentations from laymen ('S'
files), readings ('R' files) and dialogs ('D' files) form homogeneous
sub-corpora. If you expect the differences between the different
subparts to have an impact on the results of standard ABX and kaldi
analyses, you should generate a separate standardized corpus for each
of them.


Adding new corpora
==================

* Make a new Python class which inherit from
  ``abkhazia.corpus.prepare.abstract_preparator``. So far, you need to
  implement few methods to populate the transcriptions, lexicon,
  etc... See the section below and the absctract preparator code for
  detailed specifications, and the existing preparators for exemples.

* To access your new corpus from the command line, register it in
  ``abkhazia.commands.abkhazia_prepare``. An intermediate factory
  class can be defined to define additional command line arguments, or
  the default ``AbstractFactory`` class can be used (if your corpus
  prepration relies on the CMU dictionary, use instead
  ``AbstractFactoryWithCMU``.


Detailed files format
=====================

.. note::

   File formats are often, but not always, identical to `Kaldi standard
   file formats <http://kaldi-asr.org/doc/data_prep.html>`_.


1. Speech recordings
--------------------

A folder called ``wavs`` containing all the wavefiles of the corpus in
a standard mono 16-bit PCM wav format sampled at 16KHz. The standard
kaldi and ABX analyses might work with other kinds of wavefiles (in
particular other sampling frequencies) but this has not been tested.
The wavs can be either links or files.


2. List of utterances
---------------------

A text file called ``segments.txt`` containing the list of all
utterances with the name of the associated wavefiles (just the
filename, not the entire path) and if there is more than one utterance
per file, the start and end of the utterance in that wavefile
expressed in seconds (the designated segment of the audio file can
include some silence before and after the utterance).

The file should contain one entry per line in the following format::

  <utterance-id> <wav-filename> <segment-begin> <segment-end>

or if there is only one utterance in a given wavefile::

  <utterance-id> <wav-filename>

Each utterance should have its unique ``utterance-id``. Moreover,
all utterance ids must begin by a unique identifier (the
``speaker-id``) for the speaker of the utterance. In addition, all
speaker ids must have the same length.

Here is an example file with three utterances::

  sp001-sentence001 sp001.wav 53.2 55.4
  sp001-sentence005 sp001.wav 65.1 66.9
  sp109-sentence003 sp109-sentence003.wav


3. List of speakers
-------------------

A text file called ``utt2spk.txt`` containing the list of all utterances
with a unique identifier for the associated speaker (the ``speaker-id``
mentionned in the previous section). As said previously, all
utterance ids must be prefixed by the corresponding ``speaker-id``. In
addition, all speaker-ids must have the same length.

The file should contain one entry per line in the following format::

  <utterance-id> <speaker-id>

Here is an example file with three utterances::

  sp001-sentence001 sp001
  sp001-sentence005 sp001
  sp109-sentence003 sp109


If you don't have this information, or wish to hide this information to kaldi but still
conform to this dataset format, you should set each utterance to its own unique speaker ID, e.g::

  sentence001 sp001
  sentence002 sp002
  sentence003 sp003
  sentence004 sp004
  ....

4. Transcription
----------------

A text file called ``text.txt``, containing the transcription in word
units for each utterance. Word units should correspond to elements in
the phonetic dictionary (having a few out-of-vocabulary words is not a
problem). The file should contain one entry per line in the following
format::

  <utterance-id> <word1> <word2> ... <wordn>

Here is an example file with two utterances::

  sp001-sentence001 ON THE OTHER HAND
  sp003-sentence002 YOU HAVE DIFFERENT FINGERS


5. Phone inventory
------------------

An UTF-8 encoded text file called ``phones.txt`` and an optional text
file called ``silences.txt`` also UTF-8 encoded.

``phones.txt`` contains a list of each symbol used in the pronunciation
dictionary (cf. next section) with the associated IPA transcription
(https://en.wikipedia.org/wiki/International_Phonetic_Alphabet). The
idea is to use IPA transcription as consistent as possible throughout
the different corpora, speaking style, languages etc. To this effect
when mapping a knew corpus to IPA you can take inspiration from
previously mapped corpora.

In addition to the phonetic annotations, if noise or silence markers
are used in your corpus (if your using a standard pronunciation
dictionary with some read text, there won't be any silence or noise
marker in the transcriptions), you must provide the list of these
markers in a file called ``silences.txt``. Two markers will be added
automatically in all cases if they aren't already present: ``SIL`` for
optional short pauses inside or between words and ``SPN`` for spoken
noise (any out-of-vocabulary item that would be encountered during
training would automatically be transcribed by kaldi to ``SPN``). If
your corpus already contains other markers for short pauses or for
spoken noise, convert them to ``SIL`` and ``SPN`` and reciprocally, make
sure that ``SIL`` or ``SPN`` aren't already used for something else your
corpus.

The file ``phones.txt`` should contain one entry per line in the
following format::

  <phone-symbol> <ipa-symbol>

The file ``silences.txt`` should contain one entry per line in the
following format::

  <marker-symbol>

Here is an example for phones.txt::

  a a
  sh ʃ
  q ʔ

An example for silences.txt::

  SIL
  Noise

In this example ``SIL`` could have been ommited since it would have been
automatically added. ``SPN`` will be automatically added.


Phones with tonal, stress or other variants
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Having variants of a given phone such as stress or tonal variants: an
additional file is needed. By default kaldi allows parameter-tying
between HMM states of all the contextual variants of a given phone
when training triphone models. To allow parameter-tying between HMM
states of other variants of a given phone such as tonal or stress
variants you need two things:

* First, all the variants must be listed as separate items in the
  ``phones.txt`` file

* Second, you must provide a ``variants.txt`` file containing one line
  for each group of phones with tonal or stress variants in the
  following format::

    <phone_variant_1 phone_variant_2 phone_variant_n>

Note that you can also use the ``variants.txt`` file to allow
parameter-tying between states of some or all of the HMM models for
silences and noises.

For example here is a ``phones.txt`` containing 5 vowels, two of which
have tonal variants::

  a1 a˥
  a2 a˥˩
  e ə
  i i
  o1 o˧
  o2 o˩
  o3 o˥
  u u

An associated ``silences.txt`` defining a marker for speechless singing
(SIL and SPN markers will be added automatically)::

  SING

An the ``variants.txt`` grouping tonal variants and also allowing
parameter sharing between the models for spoken noise and speechless
singing::

  a1 a2
  o1 o2 o3
  SPN SING


6. Phonetic dictionary
----------------------

A text file ``lexicon.txt`` containing a list of words with their
phonetic transcription. The words should correspond to the words used
in the utterance transcriptions of the corpus; the phones should
correspond to the phones used in the original phoneset (not IPA) of
the corpus (see previous sections). The dictionary can contain more
words than necessary. Any word from the transcriptions that is not in
the dictionary will be ignored for ABX analyses and will be mapped by
kaldi to an out-of-vocabulary special item ``<unk>`` transcribed as
``SPN`` (spoken noise, see previous section). If no entry ``<unk>`` is
present in the dictionary it will be automatically added.

Depending on your purposes, the unit in the dictionary can be lexical
words (e.g. for a corpus of read speech without detailed phonetic
transcription), detailed pronunciation variants of words (e.g. for a
corpus of spontaneous speech with detailed phonetic transcription),
phonemes... The dictionary can also contain special entries for noise
and silence if they are explicitly transcribed in the corpus, as in
TIMIT for example.

Each line of the file contains the entry for a particular word, in the
following format::

  <word> <phone_1> <phone_2> ... <phone_n>

Here is an example lexicon containing two words and using the TIMIT
phoneset::

  anyone eh n iy w ah n
  monitor m aa n ah t er


7. Time-alignments (Optional)
-----------------------------

Not yet supported.

A text file called ``phone_alignment.txt``, containing a beginning and
end timestamp for each phone of each utterance in the corpus. The file
should contain one entry per line in the following format::

  <utterance-id> <phone_start> <phone_end> <phone_symbol>

The timestamps are in seconds and are given relative to the beginning
each utterance. The phone symbols correspond to those used in the
pronunciation dictionary, (not to the IPA transcriptions).

Here is an example file with two utterances containing three and two
phones respectively::

  sp001-sentence001 1.211 1.256 a1
  sp001-sentence001 1.256 1.284 t
  sp001-sentence001 1.284 1.340 o3
  sp109-sentence003 0.331 0.371 u
  sp109-sentence003 0.371 0.917 sh


8. Language model (Optional)
----------------------------

Not yet supported.


9. Syllabification (Optional)
-----------------------------

Not yet supported.
