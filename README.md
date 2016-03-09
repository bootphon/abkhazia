# Abkhazia

Tools for performing standard ABX and kaldi experiments on speech
corpora in a unified way

Documentation **actually not up to date** can be found
[here](https://github.com/bootphon/abkhazia/wiki)


## Installation

### Install dependencies

Before deploying abkahzia on your system, you need to install the
following dependencies. If they are not available on your system, the
abkhazia configuration script will fail.

* [Kaldi Speech Recognition Toolkit](http://kaldi-asr.org).

	* Install it, following installation guidelines
      [here](http://kaldi-asr.org/doc/install.html).

    * Install kaldi tools (SRILM and IRSTLM librairies) required by
      abkhazia. From your kaldi root directory, type:

            cd ./tools
            ./extras/install_irstlm.sh
            ./extras/install_srilm.sh

    * You will have to provide the Kaldi directory to abkhazia during
      configuration.

* [sox](http://sox.sourceforge.net) with flac support and
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
            sudo make install


### Install Abkahzia

First run the configuration script. It will check the dependancies for
you and will initialize a default configuration file in
`abkahzia/share/abkahzia.cfg`.

    ./configure

 Rerun this script and correct the prompted configuration errors until
 it succed. Then move to next step:

    python setup.py build
    python setup.py install

In case you want to modify an dtest the code, replace the last step by
``python setup.py develop``.


## Licence

**Copyright 2015, 2016 by Thomas Schatz, Xuan Nga Cao, Roland Thiollière, Mathieu Bernard**

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
