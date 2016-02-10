# TODO

## Installation

### Manage paths to dependancies

- [ ] test and use data-directory in code

- kaldi:
  - [X] kaldi-root in share/abkahzia.cfg
  - [ ] use it in the code -> refactor corpora/utils/utils.py
  - [ ] sph2pipe -> express it from kaldi

- CMU dictionary:
  - [X] download it during installation
  - [ ] use it in the code -> AbstractPreparatorWithCMU class

## Corpora preparation

- Smart overwrite of exitisting wavs

    Consume a lot of time, really annoying when debugging preparators
    - [X] remove the --overwrite parameter and do it by default
    - [ ] change the preparator interface to have list_audio_files() and
      convert_wavfile() instead of make_wavs()

- debug WSJ (entire corpus)

- GlobalPhone
  - [ ] debug Mandarin
  - [ ] debug Vietnamese

- test CSJ preparation !

## Corpora validation

- fix this bug of overlapping utterances (at least in
  Buckeye, see for other corpora)
