% Abkhazia -- ASR experiments made easy
% Xuan Nga Cao; Mathieu Bernard
% LSCP Bootphon Team Meeting -- March 24, 2016


# Abkhazia -- ASR experiments made easy

* Abkhazia is a Python library and a **command-line tool**

    - sources and installation instructions at
      *https://github.com/bootphon/abkhazia*
    - free software (GPL3)
    - in development (about 70% done)...

* Performs **various ASR tasks**

    - language and acoustic models, forced-alignment, decoding
    - use the Kaldi toolkit (kaldi-asr.org)
    - local or parallel computation (on the cluster)
    - uniform command-line syntax

* Defines and rely on a **standard speech corpus format**

    - inspired by Kaldi format
    - support for several corpora (WSJ, Buckeye, etc...)
    - possible extension to new corpora

# The big picture -- what abkhazia can do

![](./images/big_picture.pdf)\


# Outline

1. Abkhazia corpus format

2. Principles and usage from command-line

3. Example: force-alignment on a Buckeye subcorpus

4. Future development



# Standard speech corpus format

TODO XN

# Supported corpora

Actually, abkhazia have preparation scripts for:

* __aic__          - Articulation Index Corpus LSCP
* __buckeye__      - Buckeye Corpus of conversational speech
* __csj__          - Corpus of Spontaneous Japanese
* __globalphone__  - GlobalPhone multilingual read speech corpus
    * Mandarin, Vietnamese
* __librispeech__  - LibriSpeech ASR Corpus
* __wsj__          - Wall Street Journal ASR Corpus
* __xitsonga__     - NCHLT Xitsonga Speech Corpus


# Abkhazia commands

* ASR tasks are spread over abkhazia _commands_:
    * __prepare__  - prepare a speech corpus for use with abkhazia
    * __split__    - split a corpus in train and test subsets
    * __language__ - compute a language model
    * __train__    - train (or retrain) an acoustic model
    * __decode__   - compute phone posteriograms or transcription
    * __align__    - compute forced-aligment

* All commands share some basic functionalities
    * parameters from command-line and/or configuration file
    * logging system, help messages


# abkhazia prepare: [raw] -> [corpus]

Convert a corpus from its raw distribution to the abkhazia format

* __input__: any supported raw corpus
* __output__: abkhazia corpus in ``<output>/data``
* __options__: corpus specific
* __examples__:
    * ``abkhazia prepare wsj --help``
    * ``abkhazia prepare buckeye -v -i ./raw_buckeye``
    * ``abkhazia prepare globalphone -j 4 -l vietnamese``


# abkhazia split: [corpus] -> [corpus], [corpus]

Split a corpus in train and test subsets

* __input__: any abkhazia corpus
* __output__: test and train sets in
    * ``<output>/train/data``
    * ``<output>/test/data``
* __key options__:
    * ``--test-prop``: proportion of utterances in test set
    * ``--by-speaker``: split by speaker (default is by utterance)
* __examples__:
    * ``abkhazia split --help``
    * ``abkhazia split --by-speaker ./input_corpus``
    * ``abkhazia split -t 0.25 -r 0 buckeye``

# abkhazia language: [corpus] -> [lm]

Compute a *n-*gram language model from an abkhazia corpus

* __input__: any abkhazia corpus
* __output__: ``language_model.fst`` and a kaldi recipe dir
* __key options__:
    * ``--model-order``: n in n-grams
    * ``--model-level``: phone or word language model
* __examples__:
    * ``abkhazia language --help``
    * ``abkhazia language --model-level word -v buckeye``
    * ``abkhazia language --model-order 3 ./input_corpus``

# abkhazia train: [corpus], [lm] -> [model]

Train a standard speaker-adapted triphone HMM-GMM model from a
prepared corpus. Write the directory ``<corpus>/model``.

# abkhazia align: [model], [lm] -> [result]

Generate a forced-alignment from acoustic and language models. Write
the directory ``<corpus>/align``.

# abkhazia decode: [corpus], [model], [lm] -> [result]

Decode a prepared corpus from a HMM-GMM model and a language
model. Write the directory ``<corpus>/decode``.


# Example -- forced-alignment of a buckeye subset

TODO XN

# Conclusion

- And the answer is...
- $f(x)=\sum_{n=0}^\infty\frac{f^{(n)}(a)}{n!}(x-a)^n$
