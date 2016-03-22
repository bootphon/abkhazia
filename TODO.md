<!-- -*-org-*- this comment force org-mode in emacs -->

* Functions

 - train
   - [X] --njobs option for cluster
   - [ ] rename the command 'acoustic'
     consistant with 'language' and disambiguate split/{train,test}
   - [ ] --retrain option
     it should be possible to retrain a trained model on a new corpus
     (for instance, specifically retrain silence models, or retrain on a
     bunch of new corpus)
   - [ ] questions vs data-driven option
   - [ ] neural nets training (RT)
   - [ ] test the acoustic model
     providing WER (word error rate) for every model, eventual
     automatic parameter search ?
 - align
   - [ ] get feats.scp from acoustic_model data (and cmvn.scp ?)
     Copy files from there instead -> train and align will share the same data
   - [ ] make it work after language/train commands
   - [ ] extensive test on several lm/am
 - decode
   (test_set, acoustic_model, (language_model))
   Compute phone posteriograms or transcription. If no language_model
   provided, a default flat unigram one is constructed.  options:
   evaluate(transcription, gold) output = {posteriorgrams,
   transcription} speaker_adapt output: results (repertoire)
 - prepare
   - [ ] --keep-short-utts option
     remove short utterances here instead of during lm/am
   - [ ] word dependent position issue
     Check in validate_corpus that adding _I, _B, _E or _S suffixes to
     phones does not create conflicts, otherwise issue a warning to say
     that word_position_dependent models won't be usable.
 - feature
   Maybe we could have a separate feature command ?
 - list
   As an alternative of the README files, display what is in
   <data-directory> For each corpus: list of present data, recipes and
   results, with the parameters/path they ran from.

* Documentation

  - [ ] have more detailed command description on 'abkhazia <command>
    --help'. Assume the user doesn't know abkhazia or kaldi.
  - [ ] have a friendly error message when running a command with
    unstasfied dependancies. For exemple, trying to train a corpus
    which have not been prepared outputs 'please prepare the corpus'
  - [ ] make a install page, deeper than in readme
  - [ ] improve the 'command line' page
  - [ ] improve the 'corpus format' page
