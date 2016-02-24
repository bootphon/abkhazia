<!-- -*-org-*- this comment force org-mode in emacs -->

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

* Misc

  - have a --force option on all commands to force overwrite of
    existing dir

* Documentation

  Import wiki in docs/ and update it!
