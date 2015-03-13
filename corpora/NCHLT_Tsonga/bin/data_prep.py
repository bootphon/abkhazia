import codecs
import os.path as p


def remove_sil_ence(file_in, file_out):
	with codecs.open(file_out, mode='w', encoding='UTF-8') as out:
		for line in codecs.open(file_in, mode='r', encoding='UTF-8'):
			l = line.replace(u" SIL-ENCE", "").strip() + u"\n"
			l = l.replace(u"[s]", u"<noise>")
			out.write(l)


root = '/Users/thomas/Documents/PhD/Recherche/other_gits/abkhazia/corpora/NCHLT_Tsonga/data'
remove_sil_ence(p.join(root, 'text.txt'), p.join(root, 'text_corrected.txt'))