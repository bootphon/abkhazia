<!-- -*-org-*- this comment force org-mode in emacs -->

* Corpora preparation

  - WSJ (entire corpus) fatal error:

    fatal error: The following files are empty: ['44is060y.wav',
    '44ds060b.wav', '44js0703.wav', '44ms090x.wav']

    There is several utterance-ids used several times in 'text.txt' 5608
    - [X] no duplicates in trs input files (all have different abspath)
    - [ ] check for duplicates in different subfolders

  - Buckeye and CSJ -- Some utterances are overlapping in time

  - Librispeech

    fatal error: The following files are empty:
    ['6345-64257-0016.wav', '2428-83705-0023.wav',
    '5338-284437-0018.wav', '8842-302201-0010.wav']

  - for wav corpora, have a --copy option

    by default wav files are not converted nor copied, just linked

* Documentation

  Import wiki in docs/ and update it!
