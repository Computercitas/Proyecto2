import os
import re
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
from collections import defaultdict, Counter
import numpy as np
import json
import heapq
import time
from langdetect import detect
import sys


nltk.download('punkt')
nltk.download('stopwords')

class SPIMI:
    def __init__(self, csv_path, bloqueTamano=5000, pathTemp='indice', indexF='indexFinal.json'):
        self.data = self.cargarDatos(csv_path)
        self.letra = self.data['lyrics'].fillna('').tolist()
        self.metaData = self.data[['track_name', 'track_artist', 'track_album_name']].to_dict('records')
        self.bloqueTamano = bloqueTamano
        self.pathTemp = pathTemp
        self.indexF = indexF
        self.num_docs = len(self.letra)
        self.stop_words = set(stopwords.words('spanish')).union(set(stopwords.words('english')))
        self.stemmer = SnowballStemmer('english')
        self.tfidf_cache = defaultdict(dict)

        self.diccionario = defaultdict(list)
        self.mormas = defaultdict(float)

        if not os.path.exists(self.pathTemp):
            os.makedirs(self.pathTemp)

        if not os.path.isfile(self.indexF):
            self.construirSpimi()
            self.merge()
            self.eliminarIdx_n()
        self.cargarIndice()

    def cargarDatos(self, path):
        data = pd.read_csv(path)
        if 'lyrics' not in data.columns:
            raise ValueError("El archivo CSV debe contener una columna llamada 'lyrics'")
        return data


    def eliminarIdx_n(self):
        for bloque_file in os.listdir(self.pathTemp):
            os.remove(os.path.join(self.pathTemp, bloque_file))
        os.rmdir(self.pathTemp)

    def preProcesamiento(self, texto):
        if isinstance(texto, float):
            return [] 
        texto = re.sub(r'[^\x00-\x7F]+', '', texto) 
        texto = re.sub(r'[^\w\s]', '', texto)
        tokens = word_tokenize(texto.lower())
        tokens = [self.stemmer.stem(word) for word in tokens if word not in self.stop_words and word.isalpha()]
        return tokens

    def construirSpimi(self):
        for bloqeuID, i in enumerate(range(0, len(self.letra), self.bloqueTamano)):
            bloque = self.letra[i:i + self.bloqueTamano]
            diccionario = defaultdict(list)
            mormas = defaultdict(float)

            for doc_id, texto in enumerate(bloque):
                tokens = self.preProcesamiento(texto)
                term_freq = Counter(tokens)

                for term, freq in term_freq.items():
                    diccionario[term].append([i + doc_id, freq])
                    mormas[str(i + doc_id)] += freq ** 2

            bloque_data = {
                'diccionario': dict(diccionario),
                'mormas': dict(mormas)
            }
            if sys.getsizeof(bloque_data) <= 4 * 1024 * 1024:  # 4 MB en bytes
                bloque_path = os.path.join(self.pathTemp, f'bloque_{bloqeuID}.json')
                with open(bloque_path, 'w', encoding='utf-8') as f:
                    json.dump(bloque_data, f, ensure_ascii=False)
            else:
                print(f"El bloque {bloqeuID} excede el tamaño límite de 4 MB.")

    def merge(self):
        bloque_files = [os.path.join(self.pathTemp, f) for f in os.listdir(self.pathTemp) if f.endswith('.json')]
        term_files = {}
        mormas = defaultdict(float)

        for bloque_file in bloque_files:
            with open(bloque_file, 'r', encoding='utf-8') as f:
                bloque_data = json.load(f)
                diccionario = bloque_data['diccionario']
                bloque_mormas = bloque_data['mormas']

                for term, postings in diccionario.items():
                    if term not in term_files:
                        term_files[term] = os.path.join(self.pathTemp, f'{term}.tmp')
                    with open(term_files[term], 'a', encoding='utf-8') as term_file:
                        for posting in postings:
                            term_file.write(f"{posting[0]}:{posting[1]}\n")

            for doc_id, norm in bloque_mormas.items():
                mormas[int(doc_id)] += norm

        term_postings = defaultdict(list)
        for term, file_path in term_files.items():
            with open(file_path, 'r', encoding='utf-8') as f:
                postings = [line.strip().split(':') for line in f]
                term_postings[term] = [[int(doc_id), int(freq)] for doc_id, freq in postings]

        mormas = {int(doc_id): np.sqrt(norm) for doc_id, norm in mormas.items()}

        final_index = {
            'diccionario': dict(term_postings),
            'mormas': mormas
        }
        with open(self.indexF, 'w', encoding='utf-8') as f:
            json.dump(final_index, f, ensure_ascii=False)
            
        for term_file in term_files.values():
            os.remove(term_file)


    def cargarIndice(self):
        with open(self.indexF, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.diccionario = defaultdict(list, data['diccionario'])
            self.mormas = {int(k): v for k, v in data['mormas'].items()}

    def calcularTFIDF(self, term, doc_id):
        if term in self.tfidf_cache and doc_id in self.tfidf_cache[term]:
            return self.tfidf_cache[term][doc_id]

        term_postings = self.diccionario.get(term, [])
        doc_freq = len(term_postings)
        tf = next((freq for doc, freq in term_postings if doc == doc_id), 0)
        idf = np.log(self.num_docs / (1 + doc_freq))
        tfidf = tf * idf

        self.tfidf_cache[term][doc_id] = tfidf
        return tfidf

    def similitudCoseno(self, query):
        query_tokens = self.preProcesamiento(query)
        query_vector = Counter(query_tokens)

        query_tfidf_vector = {}
        query_norm = 0.0
        for term, count in query_vector.items():
            if term in self.diccionario:
                idf = np.log(self.num_docs / (1 + len(self.diccionario[term])))
                query_tfidf = count * idf
                query_tfidf_vector[term] = query_tfidf
                query_norm += query_tfidf ** 2

        query_norm = np.sqrt(query_norm) or 1.0

        scores = defaultdict(float)

        for term, query_tfidf in query_tfidf_vector.items():
            query_tfidf /= query_norm
            if term in self.diccionario:
                for doc_id, freq in self.diccionario[term]:
                    doc_tfidf = self.calcularTFIDF(term, doc_id) / self.mormas[doc_id]
                    scores[doc_id] += query_tfidf * doc_tfidf

        return scores

    def busqueda_topK(self, query, k=5, additional_features=None):
        if additional_features is None:
            additional_features = []

        start_time = time.time()
        scores = self.similitudCoseno(query)
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_k_results = sorted_scores[:k]

        results = []
        for doc_id, score in top_k_results:
            metadata = self.metaData[doc_id]
            result = {
                'track_name': metadata['track_name'],
                'row_position': doc_id+2,
                'similitudCoseno': score
            }
            for feature in additional_features:
                if feature in self.data.columns:
                    result[feature] = self.data.iloc[doc_id][feature]
            results.append(result)

        end_time = time.time()

        return {
            'query_time': end_time - start_time,
            'results': results
        }
# Uso
spimi = SPIMI(csv_path='spotify_songs.csv')
# Busqueda
#query = 'love'
#result = spimi.busqueda_topK(query, k=5)
#print(result)
