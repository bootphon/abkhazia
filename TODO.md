# TODO

## Installation

### Manage paths to dependancies

fix some paths at installation (in a config file):
- path to kaldi
- path to CMUdict
- path to flac, sox, shorten

### Download 3rd party code and data

- cmu dict
- sph2pipe
- shorten

## Corpora preparation

- remove cmu_dict parameter and feed it during installation

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
