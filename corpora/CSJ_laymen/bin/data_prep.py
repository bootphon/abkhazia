# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 01:52:19 2015

@author: Thomas Schatz
"""

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

"""

MoraId == number or x or φ ??
TagUncertainEnd=1
TagUncertainStart=1
<Noise
<NonLinguisticSound
LUWDictionaryForm=xxx(+)

Alignment of various levels (sentences and phones)
For 8 files: bad portions ???
"""

# get info about speakers (M/F) into utt2spk and change name of files for more consistency
# what about non-core files?
def parse_CSJ_xml(xml_file):
	tree = ET.ElementTree(file=xml_file)
	talk = tree.getroot()
	talk_id = talk.attrib["TalkID"]	
	speaker = talk.attrib["SpeakerID"]
	gender = talk.attrib["SpeakerSex"]
	
	if talk_id[0] == "D":
		is_dialog = True
		sentenceChannel = []
	else:
		is_dialog = False

	for ipu in talk.iter("IPU"):
		ipu.attrib["IPUStartTime"]
		ipu.attrib["IPUEndTime"]
		ipu.attrib["Channel"]
		ipu.attrib["IPUID"]
		for phoneme in ipu.iter("Phoneme"):
			phoneme.attrib["PhonemeID"]
			phoneme.attrib["PhonemeEntity"]

xml_file = "/Users/thomas/Documents/PhD/Recherche/databases/CSJ/S07M0833.xml"
parse_CSJ_xml(xml_file)