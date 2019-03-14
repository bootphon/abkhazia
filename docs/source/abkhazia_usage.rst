=================
Command-line tool
=================

Once abkhazia is installed on your system, use it from a terminal with
the ``abkhazia`` command. For now, type::

  abkhazia --help

As you see, the program is made of several subcommands which are
detailed below. It also read a configuration file (the default one is
installed with abkhazia and you can overload it by specifying the
``--config <config-file>`` option.


Commands
========

For more details on a specific command, type ``abkhazia <command>
--help``.


validate: [corpus]
------------------

Check if a corpus stored on disk is in a valid format and ready to be
used by abkhazia.

prepare: [raw] -> [corpus]
--------------------------

Prepare a speech corpus from its raw distribution format to the
abkhazia format. Write the directory ``<corpus>/data``.

split: [corpus] -> [corpus], [corpus]
-------------------------------------

Split a speech corpus in train and test sets. Write the directories
``<corpus>/train`` and ``<corpus>/test``.

language: [corpus] -> [lm]
--------------------------

Generate a language model from a prepared corpus. Write the directory
``<corpus>/language``.

features: [corpus] -> [features]
--------------------------------

Compute speech features on the given corpus. Write the directory
``<corpus>/features``.

acoustic: [corpus], [features] -> [model]
-----------------------------------------

Train an acoustic model from a prepared corpus and its features. Write
the directory ``<corpus>/model``.

align: [corpus], [model], [lm] -> [result]
------------------------------------------

Generate a forced-alignment from acoustic and language models. Write
the directory ``<corpus>/align``.

decode: [corpus], [model], [lm] -> [result]
-------------------------------------------

Decode a prepared corpus from a HMM-GMM model and a language
model. Write the directory ``<corpus>/decode``.
