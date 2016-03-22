<!-- -*-org-*- this comment force org-mode in emacs -->

* Functions

 - [-] train
   - [X] symlink the last model directory (storing the target acoustic
     model) to exp/acoustic_model
   - [ ] --retrain option
     it should be possible to retrain a trained model on a new corpus
     (for instance, specifically retrain silence models, or retrain on a
     bunch of new corpus)
   - [ ] questions vs data-driven option
   - [ ] test the acoustic model
     providing WER for every model, eventual automatic parameter search ?
 - [-] align
   - [X] remove the language model part from the recipe
   - [X] remove the training part from the recipe
   - [X] read acoustic model from exp/acoustic_model
   - [X] make it work after language/train commands
   - [ ] extensive test on several lm/am
 - decode(test_set, acoustic_model, (language_model))
   Compute phone posteriograms or transcription. If no language_model
   provided, a default flat unigram one is constructed.  options:
   evaluate(transcription, gold) output = {posteriorgrams,
   transcription} speaker_adapt output: results (repertoire)
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
