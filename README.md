# Abkhazia

Tools for performing standard ABX and kaldi experiments on speech
corpora in a unified way

Documentation **ACTUALLY NOT UP TO DATE** can be found
[here](https://github.com/bootphon/abkhazia/wiki)


## Installation

### 1. Install dependencies

Before deploying abkahzia on your system, you need to install the
following dependencies. If they are not available on your system, the
abkhazia configuration script will fail.

#### 1.1. [Kaldi Speech Recognition Toolkit](http://kaldi-asr.org).

* **In brief: install_kaldi.sh**

    the ``./install_kadi.sh`` will download, configure
    and compile kaldi to ``./kaldi``. This should work on any
    standard Unix distribution and fail on the first encountered
    error. If so, install kaldi manually as detailed in the
    following steps.

* **If install_kaldi.sh failed**

    Install it by hand, with the following steps

    * Because Kaldi is developed under continuous integration, there is no
      published release to rely on. To ensure the abkhazia stability, we
      therefore maintain a Kaldi fork that is guaranteed to work. Clone it
      in a directory of your choice and ensure the active branch is
      *abkhazia* (this should be the default):

            git clone git@github.com:bootphon/kaldi.git

    * Once cloned, you have to install Kaldi (configuration and
      compilation). Follow the instructions from
      [here](http://kaldi-asr.org/doc/install.html). Basically, you have
      to do (from the `kaldi` directory):

            cd tools
            ./extras/check_dependancies.sh
            make -j 4  # -j N does a parallel build on N CPUs
            cd ../src
            ./configure
            make depend -j 4
            make -j 4

    * Install kaldi extras tools (SRILM and IRSTLM librairies)
      required by abkhazia. From your local kaldi directory, type:

            cd ./tools
            ./extras/install_irstlm.sh
            ./extras/install_srilm.sh

#### 1.2. flac, sox and shorten

Abkhazia relies on [flac](https://xiph.org/flac),
[sox](http://sox.sourceforge.net) and
[shorten](http://etree.org/shnutils/shorten) for wav conversion from
various audio formats.

* sox and flac should be in repositories of every standard Unix
  distribution, for exemple in Debian/Ubuntu:

        sudo apt-get install flac sox

* shorten must be installed manually, follow these steps to
  download, compile and install it:

        wget http://etree.org/shnutils/shorten/dist/src/shorten-3.6.1.tar.gz
        tar xzf shorten-3.6.1.tar.gz
        cd shorten-3.6.1
        ./configure
        make
        [sudo] make install

#### 1.3. festival

* You need to install
  [festival](http://www.cstr.ed.ac.uk/projects/festival) on your
  system. Visit
  [this link](http://www.festvox.org/docs/manual-2.4.0/festival_6.html#Installation)
  for installation guidelines.

* On Debian/Ubuntu simply run:

        [sudo] apt-get install festival

### 2. Install Abkhazia

* First run the configuration script. It will check the dependancies for
  you and will initialize a default configuration file in
  `abkahzia/abkhazia.cfg`.

        ./configure

  Rerun this script and correct the prompted configuration errors
  until it succed. At least you are asked to specify the path to kaldi
  (from step 1.1) in the configuration file.

* Then install abkhazia

        python setup.py build
        [sudo] python setup.py install

* In case you want to modify and test the code, replace the last step by
  ``python setup.py develop``.


## Licence

**Copyright 2015, 2016 by Mathieu Bernard, Thomas Schatz, Xuan Nga Cao, Roland Thiollière, Emmanuel Dupoux**

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
