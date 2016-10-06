==============================
Installation and configuration
==============================


.. note::

   First of all, clone the Abkhazia github repository and go to the
   created ``abkhazia`` directory::

     git clone git@github.com:bootphon/abkhazia.git
     cd ./abkhazia


Install dependencies
====================

Before deploying Abkahzia on your system, you need to install the
following dependencies: Kaldi, sox, shorten and festival.

Kaldi
-----

* **In brief: use install_kaldi.sh**

    The ``./install_kaldi.sh`` script will download, configure and
    compile Kaldi to ``./kaldi``. This should work on any standard
    Unix distribution and fail on the first encountered error. If so,
    install Kaldi manually as detailed in the following steps.

* **If install_kaldi.sh failed**

    If so you need to install Kaldi manually with the following steps:

    * Because Kaldi is developed under continuous integration, there
      is no published release to rely on. To ensure the abkhazia
      stability, we therefore maintain a Kaldi fork that is guaranteed
      to work. Clone it in a directory of your choice and ensure the
      active branch is *abkhazia* (this should be the default)::

            git clone git@github.com:bootphon/kaldi.git

    * Once cloned, you have to install Kaldi (configuration and
      compilation). Follow the instructions from
      `here <http://kaldi-asr.org/doc/install.html>`_. Basically, you have
      to do (from the ``kaldi`` directory)::

            cd tools
            ./extras/check_dependancies.sh
            make -j  # -j does a parallel build on multiple cores
            cd ../src
            ./configure
            make depend -j
            make -j

    * Install Kaldi extras tools (SRILM and IRSTLM librairies)
      required by abkhazia. From your local kaldi directory, type::

            cd ./tools
            ./extras/install_irstlm.sh
            ./extras/install_srilm.sh

Flac, sox and festival
----------------------

* Abkhazia relies on `flac <https://xiph.org/flac>`_ and `sox
  <http://sox.sourceforge.net>`_ for audio conversion from various file
  formats to wav.

  They should be in repositories of every standard Unix distribution,
  for exemple in Debian/Ubuntu::

    sudo apt-get install flac sox

* Abkhazia also needs `festival
  <http://www.cstr.ed.ac.uk/projects/festival>`_ to phonemize the
  transcriptions of the Childes Brent corpus. Visit `this link
  <http://www.festvox.org/docs/manual-2.4.0/festival_6.html#Installation>`_
  for installation guidelines, or on Ubuntu/Debian use::

    sudo apt-get install festival


Shorten
-------

`shorten <http://etree.org/shnutils/shorten>`_ is used for wav
conversion from the original *shn* audio files, it must be installed
manually. Follow these steps to download, compile and install it::

    wget http://etree.org/shnutils/shorten/dist/src/shorten-3.6.1.tar.gz
    tar xzf shorten-3.6.1.tar.gz
    cd shorten-3.6.1
    ./configure
    make
    sudo make install


Install Abkhazia
================


* Run the configuration script. It will check the dependancies for
  you and will initialize a default configuration file in
  ``abkahzia/abkhazia.cfg``::

    ./configure

  Rerun this script and correct the prompted configuration errors
  until it succed. At least you are asked to specify the path to Kaldi
  (as installed in previous step) in the configuration file.

* Finally install abkhazia::

    python setup.py build
    [sudo] python setup.py install

  In case you want to modify and test the code inplace, replace the
  last step by ``python setup.py develop``.

* To build the documentation (the one you are actually reading),
  install ``sphinx`` (with ``pip install Sphinx``) and, from the
  Abkhazia root directory, have a::

    sphinx-build -b html ./docs/source ./docs/html

  Then open the file ``./docs/html/index.html`` with your favorite browser.


Run the tests
=============

.. note::

   The tests are actually based on the Buckeye corpus, so you must
   provide the path to the raw Buckeye distribution before launching the
   tests. Enter this path in the ``buckeye-directory`` entry in the
   Abkhazia configuration file.

* Abkhazia comes with a test suite, from the abkhazia root directory run
  it using::

    pytest ./test

* To install the ``pytest`` package, simply have a::

    [sudo] pip install pytest

* If you run the tests on a cluster and you configured Abkhazia to use
  Sun GridEngine, you must specify the temp directory to be in a shared
  filesystem with ``py.test ./test --basetemp=mydir``.


.. _kaldi: http://kaldi-asr.org
