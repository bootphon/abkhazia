<!-- -*-org-*- this comment force org-mode in emacs -->

* Structure and usage

  - [ ] fix log file in abstractrecipe to go in <corpus>/logs
  - [ ] Generate a README during each abkhazia operation

* Corpora preparation

  - WSJ

    - entire corpus, -s 1, -s 2, -s 3
      There is several utterance-ids used several times in 'text.txt' 5608
      - [X] no duplicates in trs input files (all have different abspath)
      - [ ] check for duplicates in different subfolders

  - Buckeye

    - XN fixing new directory structure
    - Some utterances are overlapping in time

  - CSJ

    Some utterances are overlapping in time, some overlaps are 2, only
    one is 3. Is it a problem ?

* Functions

 - [X] split(abkhazia_corpus, train_proportion)

   split corpus in test and train sets

   options: split randomly vs split while respecting speakers?
   output: abkhazia_corpus_train, abkhazia_corpus_test
   note:
    pourquoi pas un split plus général, eg, pour faire dev/train/test ?
    this would be split_corpus(abkhazia_corpus,name1,prop1,name2,prop2 …
    nameN,propN

 - [ ] lang(abkhazia_corpus):

   Train a language model

   options: unigram, bigram
   output: language_model(repertoire), readmefile, kaldi format

 - [ ] align(abkhazia_corpus)

   Forced alignment

   - [ ] test/debug at least on xitsonga, wsj
   - [ ] remove the language model part from the recipe (this will be
     the 'abkhazia lang' command)
   - [ ] integrate the kaldi2abkhazia conversion script as the final
     step of ForceAlign.run()

 - [ ] train(train_set):

  Train an acoustic model (and a simple language model if not provided)
  and test it (providing WER for every model, eventual automatic
  parameter search ?)

  options:
  model type = {monophone, triphone, neural network}
  features = mfcc, mfcc+pitch or custom features (link to the feature_extraction package ?)
  model parameters (eg, nb of mixtures, nb of triphones, questions vs data-driven,speaker_readapt)
  output: acoustic_model (répertoire + readme)
  retrain(train_set, acoustic_model)

 - [ ] decode(test_set, acoustic_model, (language_model)):

  Compute phone posteriograms or transcription. If no language_model
   provided, a default flat unigram one is constructed

  options:
  evaluate(transcription, gold)
  output = {posteriorgrams, transcription}
  speaker_adapt
  output: results (repertoire)

* Documentation

  Import wiki in docs/ and update it!

* NOTES (DPX)

 - feature extraction

   Maybe we could have a separate feature extraction package that
   takes an abkhazia_wav_corpus as input and outputs an
   abkhazia_feat_corpus?  (or should be the feature file be a separate
   one?

 - retraining

   it should be possible to retrain a trained model on a new corpus
   (for instance, specifically retrain silence models, or retrain on a
   bunch of new corpus) Formats: features
