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
from bisect import bisect_left #búsqueda binaria

nltk.download('punkt_tab')
nltk.download('stopwords')

class SPIMI:
    def __init__(self, csv_path, bloqueTamano=5000, pathTemp='indice', indexF='indexFinal.json'):
        self.data = self.cargarDatos(csv_path)
        self.letra = self.data['lyrics'].fillna('').tolist()
        self.metaData = self.data[['track_id', 'track_name', 'track_artist', 'lyrics', 'track_album_name']].to_dict('records')
        self.bloqueTamano = bloqueTamano
        self.pathTemp = pathTemp
        self.indexF = indexF
        self.num_docs = len(self.letra)
        self.stop_words = set(stopwords.words('spanish')).union(set(stopwords.words('english')))
        self.stemmer = SnowballStemmer('english')
        self.tfidf_cache = defaultdict(dict)

        self.indiceInvertido = defaultdict(list)
        self.normas = defaultdict(float)

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
            indiceInvertido = defaultdict(list)
            normas = defaultdict(float)

            for doc_id, texto in enumerate(bloque):
                tokens = self.preProcesamiento(texto)
                term_freq = Counter(tokens)

                for term, freq in term_freq.items():
                    indiceInvertido[term].append([i + doc_id, freq])
                    normas[str(i + doc_id)] += freq ** 2

            bloque_data = {
                'indiceInvertido': dict(indiceInvertido),
                'normas': dict(normas)
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
        normas = defaultdict(float)

        for bloque_file in bloque_files:
            with open(bloque_file, 'r', encoding='utf-8') as f:
                bloque_data = json.load(f)
                indiceInvertido = bloque_data['indiceInvertido']
                bloque_normas = bloque_data['normas']

                for term, postings in indiceInvertido.items():
                    if term not in term_files:
                        term_files[term] = os.path.join(self.pathTemp, f'{term}.tmp')
                    with open(term_files[term], 'a', encoding='utf-8') as term_file:
                        for posting in postings:
                            term_file.write(f"{posting[0]}:{posting[1]}\n")

            for doc_id, norm in bloque_normas.items():
                normas[int(doc_id)] += norm

        term_postings = defaultdict(list)
        for term, file_path in term_files.items():
            with open(file_path, 'r', encoding='utf-8') as f:
                postings = [line.strip().split(':') for line in f]
                term_postings[term] = [[int(doc_id), int(freq)] for doc_id, freq in postings]

        normas = {int(doc_id): np.sqrt(norm) for doc_id, norm in normas.items()}

        #ordenar índices por orden alfabetico de las palabras
        sorted_term_postings = sorted(dict(term_postings).items(), key=lambda item: item[0])
        
        final_index = { #concatenar todo en un mismo archivo 
            'indiceInvertido': sorted_term_postings, #diccionario con el índice invertido
            'normas': normas #diccionario de normas
        }
        with open(self.indexF, 'w', encoding='utf-8') as f: #guardar en memoria secundaria
            json.dump(final_index, f, ensure_ascii=False)
            
        for term_file in term_files.values(): #remover archivos temporales
            os.remove(term_file)


    def cargarIndice(self):
        with open(self.indexF, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.indiceInvertido = defaultdict(list, data['indiceInvertido'])
            self.normas = {int(k): v for k, v in data['normas'].items()}

    def calcularTFIDF(self, term, doc_id):
        if term in self.tfidf_cache and doc_id in self.tfidf_cache[term]:
            return self.tfidf_cache[term][doc_id]

        term_postings = self.indiceInvertido.get(term, [])
        doc_freq = len(term_postings)
        tf = next((freq for doc, freq in term_postings if doc == doc_id), 0)
        idf = np.log(self.num_docs / (1 + doc_freq))
        tfidf = tf * idf

        self.tfidf_cache[term][doc_id] = tfidf
        return tfidf

    def binary_search(self, term): #busqueda binaria en el índice invertido ordenado
        keys_list = list(self.indiceInvertido.keys())
        i = bisect_left(keys_list, term)
        if i != len(keys_list) and keys_list[i] == term:
            return self.indiceInvertido[term]
        return None  

    def similitudCoseno(self, query):
        query_tokens = self.preProcesamiento(query)
        query_vector = Counter(query_tokens)

        query_tfidf_vector = {}
        query_norm = 0.0
        for term, count in query_vector.items():
            if term in self.indiceInvertido:
                idf = np.log(self.num_docs / (1 + len(self.indiceInvertido[term])))
                query_tfidf = count * idf
                query_tfidf_vector[term] = query_tfidf
                query_norm += query_tfidf ** 2

        query_norm = np.sqrt(query_norm) or 1.0

        scores = defaultdict(float)

        for term, query_tfidf in query_tfidf_vector.items():
            query_tfidf /= query_norm
            if self.binary_search(term) != None: # en vez de iterar linealmente con if term *in* self.indiceInvertido
                for doc_id, freq in self.indiceInvertido[term]:
                    doc_tfidf = self.calcularTFIDF(term, doc_id) / self.normas[doc_id]
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
                'track_id': metadata['track_id'],
                'track_name': metadata['track_name'],
                'track_artist': metadata['track_artist'],
                'lyrics': metadata['lyrics'][:25] + "...",
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
spimi = SPIMI(csv_path='./backend/data/spotify_songs.csv')
# Busqueda
query = 'live laugh love people hello'
result = spimi.busqueda_topK(query, k=5)
print(result)
