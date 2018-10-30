import os

import nltk

BASE_DIR = os.path.dirname(__file__)

print "Downloading nltk corpus: punkt ..."
status = nltk.download('punkt')
if not status:
    print "punkt Download was unsucessful"

print "Downloading nltk corpus: wordnet ..."
status = nltk.download('wordnet')
if not status:
    print "wordnet Download was unsucessful"

print "Downloading nltk corpus: MaxEnt POS ..."
status = nltk.download('maxent_treebank_pos_tagger')
if not status:
    print "MaxEnt POS Download was unsucessful"

print "Downloading nltk corpus: AP POS Tagger..."
status = nltk.download('averaged_perceptron_tagger')
if not status:
    print "AP POS Tagger Download was unsucessful"
