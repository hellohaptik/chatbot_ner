import requests
import gzip
import csv
import os, os.path
import json
import requests
# import pandas as pd
import nltk
from nltk import word_tokenize, pos_tag
import re
from model.constant import RES



print '1'
os.system('bash model/crf/exec.sh')
print RES
