import os
# NLTK: Procesamiento de lenguaje natural
import nltk
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

import numpy as np
import pandas as pd

from collections import Counter

nltk.download('stopwords')
