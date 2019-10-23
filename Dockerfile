FROM ubuntu:18.04

ENV TZ=America/New_York \
    DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# install sotware dependencies
RUN apt-get update && apt-get install --no-install-recommends -y -qq \
        automake \
        autoconf \
        bzip2 \
        clang-3.9 \
        espeak-ng \
        festival \
        flac \
        g++ \
        gawk \
        gcc \
        gfortran \
        git \
        gzip \
        libatlas3-base \
        libtool \
        make \
        patch \
        perl \
        python2.7 \
        python3 \
        python3-h5py \
        python3-joblib \
        python3-matplotlib \
        python3-numpy \
        python3-pip \
        python3-pytest \
        python3-scipy \
        python3-setuptools \
        python3-sphinx \
        sox \
        subversion \
        wget \
        zlib1g-dev && \
      rm -rf /var/lib/apt/lists/*

# install shorten
RUN wget http://shnutils.freeshell.org/shorten/dist/src/shorten-3.6.1.tar.gz && \
      tar xzf shorten-3.6.1.tar.gz && \
      cd shorten-3.6.1 && \
      ./configure && \
      make && \
      make install && \
      cd - && \
      rm -rf shorten*

# install kaldi
WORKDIR /kaldi
RUN export ncores=4 && \
      ln -s /usr/bin/python2.7 /usr/bin/python && \
      ln -s -f bash /bin/sh && \
      git clone --branch abkhazia --single-branch https://github.com/bootphon/kaldi.git . && \
      # compile kaldi tools
      cd /kaldi/tools && \
      ./extras/check_dependencies.sh && \
      sed -i "s/CXX = g++/# CXX = g++/" Makefile && \
      sed -i "s/# CXX = clang++/CXX = clang++-3.9/" Makefile && \
      sed -i "s/OPENFST_VERSION = 1.3.4/# OPENFST_VERSION = 1.3.4/" Makefile && \
      sed -i "s/# OPENFST_VERSION = 1.4.1/OPENFST_VERSION = 1.4.1/" Makefile && \
      make -j $ncores && \
      ./extras/install_openblas.sh && \
      # compile kaldi src
      cd /kaldi/src && \
      ./configure --openblas-root=../tools/OpenBLAS/install && \
      sed -i "s/\-g # -O0 -DKALDI_PARANOID.*$/-O3 -DNDEBUG/" kaldi.mk && \
      sed -i "s/ -rdynamic//g" kaldi.mk && \
      sed -i "s/g++/clang++-3.9/" kaldi.mk && \
      make depend -j $ncores && \
      make -j $ncores && \
      # compile irstlm
      cd /kaldi/tools/extras && \
      rm -f install_irstlm.sh && \
      wget https://raw.githubusercontent.com/kaldi-asr/kaldi/master/tools/extras/install_irstlm.sh && \
      chmod +x install_irstlm.sh && \
      wget https://raw.githubusercontent.com/kaldi-asr/kaldi/master/tools/extras/irstlm.patch && \
      cd /kaldi/tools && \
      ./extras/install_irstlm.sh && \
      # compile srilm
      wget https://github.com/denizyuret/nlpcourse/raw/master/download/srilm-1.7.0.tgz -O srilm.tgz && \
      ./extras/install_srilm.sh

# clone and install abkhazia
WORKDIR /abkhazia
RUN git clone https://github.com/bootphon/abkhazia.git . && \
      KALDI_PATH=/kaldi ./configure && \
      python3 setup.py build && \
      python3 setup.py install
