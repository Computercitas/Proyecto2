import os
import re
import pandas as pd
import csv
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
from collections import defaultdict, Counter
import numpy as np
import json
import math
import heapq
import time
from langdetect import detect
import sys
from bisect import bisect_left

nltk.download('punkt_tab')
nltk.download('stopwords')

class SPIMI:
    def __init__(self, csv_path, pathTemp='indice', indexF='indexFinal.json'):
        self.csv_path = csv_path
        self.mb_per_block = 4 * 1024 * 16 #4MB
        #self.data = self.cargarDatos(csv_path)               #TODO: Change this
        #self.letra = self.data['lyrics'].fillna('').tolist() #TODO: Change this 
        #self.metaData = self.data[['track_id', 'track_name', 'track_artist', 'lyrics', 'track_album_name']].to_dict('records') #TODO: Change this
        self.total_docs = 0
        self.pathTemp = pathTemp
        self.indexF = indexF
        self.stop_words = set(stopwords.words('spanish')).union(set(stopwords.words('english')))
        self.stemmer = SnowballStemmer('english')
        self.tfidf_cache = defaultdict(dict)
        self.build_time = 0  # Para medir el tiempo de construcción del índice

        self.diccionario = defaultdict(list)
        self.normas = defaultdict(float)

        if not os.path.exists(self.pathTemp):
            os.makedirs(self.pathTemp)

        if not os.path.isfile(self.indexF):
            self.construirSpimi(self.mb_per_block)
            self.merge()
            #self.eliminarIdx_n() 
            print("Tiempo de construcción del índice para ", self.total_docs, " documentos: ", round(self.build_time, 2)*1000, "ms")

        #self.cargarIndice()

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

    def construirSpimi(self, limite_mb_bloque):
        start_time = time.perf_counter() # Para medir el tiempo de construcción
        block_number = 0
        start_line = 0
        while True:  # Creo bloques hasta haber leído todo el csv
            diccionario = defaultdict(list)  # Índice invertido (diccionario con tokens, frecuencias y IDs de documento)
            normas = defaultdict(float)      # Diccionario de normas
            
            with open(self.csv_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)    # Iterador para leer línea por línea
                for _ in range(start_line):  # Salta hasta la línea donde quedamos en la iteración anterior
                    next(reader, None)

                for i, row in enumerate(reader, start=start_line + 1):  # Continúa desde la última línea leída
                    self.total_docs += 1 #Contar número de docs en el csv (usado en otras funciones)
                    if sys.getsizeof(diccionario) + sys.getsizeof(normas) >= limite_mb_bloque:  # Verificar si queda espacio en el bloque
                        break
                    
                    tokens = Counter(self.preProcesamiento(row[3]))  # Preprocesar la letra (cuarta columna) y contar frecuencia
                    for term, freq in tokens.items():
                        diccionario[term].append([i, freq])  # i es el docId (línea que estamos leyendo)
                        normas[str(i)] += freq ** 2

            bloque_data = {'diccionario': dict(diccionario), 'normas': dict(normas)}  # Concateno normas e índice invertido

            # Guardar bloque en un archivo JSON
            bloque_path = os.path.join(self.pathTemp, f'bloque_{block_number}.json')
            with open(bloque_path, 'w', encoding='utf-8') as f:
                json.dump(bloque_data, f, ensure_ascii=False)

            # Preparar para el siguiente bloque
            start_line = i + 1  # Continuar desde la última línea leída
            block_number += 1

            # Si no llegué a llenar el bloque, significa que ya no hay más documentos que leer.
            if sys.getsizeof(diccionario) + sys.getsizeof(normas) < limite_mb_bloque:
                break

        end_time = time.perf_counter()
        self.build_time = end_time - start_time #Le voy a sumar el merge a esto, ya que es parte de la construcción

    def merge(self):
        start_time = time.perf_counter() #Para ver el tiempo del merge (parte de la construcción del índice)

        bloque_files = [os.path.join(self.pathTemp, f) for f in os.listdir(self.pathTemp) if f.endswith('.json')]
        normas = defaultdict(float)

        for bloque_file in bloque_files:
            with open(bloque_file, 'r', encoding='utf-8') as f:
                bloque_data = json.load(f)
                diccionario = bloque_data['diccionario']
                bloque_normas = bloque_data['normas']

                sorted_dict = sorted(dict(diccionario).items(), key=lambda item: item[0])

            for doc_id, norm in bloque_normas.items():
                normas[int(doc_id)] += norm

            sorted_block = {
            'diccionario': sorted_dict,
            'normas': normas
            }
            with open(bloque_file, 'w', encoding='utf-8') as file:
                json.dump(sorted_block, file, ensure_ascii=False)

        end_time = time.perf_counter()
        self.build_time += (end_time - start_time) #Sumo al tiempo de construcción del índice

    def cargarIndice(self):
        with open(self.indexF, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.diccionario = defaultdict(list, data['diccionario'])
            self.normas = {int(k): v for k, v in data['normas'].items()}

    """
    def calcularTFIDF(self, term, doc_id):
        if term in self.tfidf_cache and doc_id in self.tfidf_cache[term]:
            return self.tfidf_cache[term][doc_id]

        term_postings = self.diccionario.get(term, [])
        doc_freq = len(term_postings)
        raw_tf = next((freq for doc, freq in term_postings if doc == doc_id), 0)
        tf = 1 + np.log(raw_tf) if raw_tf > 0 else 0
        idf = np.log(self.total_docs / (1 + doc_freq))
        tfidf = tf * idf
        self.tfidf_cache.setdefault(term, {})[doc_id] = tfidf
        return tfidf

    def binary_search(self, term):
        keys_list = list(self.diccionario.keys())
        i = bisect_left(keys_list, term)
        if i != len(keys_list) and keys_list[i] == term:
            return self.diccionario[term]
        return None  

    def similitudCoseno(self, query):
        query_tokens = self.preProcesamiento(query)  # Preprocesamos la query
        query_vector = Counter(query_tokens)  # TF de los tokens de la query
        query_tfidf_vector = {}
        query_norm = 0.0

        # Obtener lista de archivos de bloque y términos en el diccionario
        bloque_files = [os.path.join(self.pathTemp, f) for f in os.listdir(self.pathTemp) if f.endswith('.json')]

        # Iterar sobre términos de la consulta
        for term, count in query_vector.items():
            for bloque_file in bloque_files:  # TODO: Aprovechar que los bloques están ordenados e ir directamente al bloque del termino
                with open(bloque_file, 'r', encoding='utf-8') as f:
                    bloque_data = json.load(f)
                    diccionario = bloque_data['diccionario']

                    if term in diccionario:  # Si el término se encuentra en el bloque actual
                        # Calcular IDF para el término
                        idf = np.log(self.total_docs / (1 + len(self.diccionario[term])))
                        query_tfidf = (1 + np.log(count)) * idf
                        query_tfidf_vector[term] = query_tfidf
                        query_norm += query_tfidf ** 2
                        break  # Salir del bucle del bloque si ya encontramos el término

        query_norm = np.sqrt(query_norm) if query_norm > 0 else 1.0

        # Calcular la similitud de coseno
        scores = defaultdict(float)
        for term, query_tfidf in query_tfidf_vector.items():
            normalized_query_tfidf = query_tfidf / query_norm
            for bloque_file in bloque_files: #verifico
                with open(bloque_file, 'r', encoding='utf-8') as f:
                    bloque_data = json.load(f)
                    diccionario = bloque_data['diccionario']
                    if term in diccionario: # Si el término se encuentra en el bloque actual
                        for doc_id, freq in self.diccionario[term]:
                            if self.normas[doc_id] != 0:
                                doc_tfidf = self.calcularTFIDF(term, doc_id)  # TF-IDF del documento
                                normalized_doc_tfidf = doc_tfidf / np.sqrt(self.normas[doc_id])  # Normalización por la norma del documento
                                scores[doc_id] += normalized_query_tfidf * normalized_doc_tfidf
        return scores
    """
    
    def compute_tf_idf(self, tf, df):
        return tf * math.log(self.total_docs / (df + 1))  # Evitar división por cero

    def similitudCoseno(self, query, k):
        # 1. Preprocesar la query
        query_tokens = self.preProcesamiento(query)
        query_tf = Counter(query_tokens)  # Frecuencia de términos en la query

        # 2. Identificar bloques relevantes (que contentan términos de la query)
        bloques_relevantes = self.get_relevant_blocks(query_tokens)

        # 3. Inicializar heap para top-k
        top_k_heap = []  # Usaremos un heap para mantener los top-k documentos

        # 4. Iterar sobre los bloques
        for bloque_file in bloques_relevantes:
            with open(bloque_file, 'r', encoding='utf-8') as f:
                bloque_data = json.load(f)
                diccionario = bloque_data['diccionario']
                bloque_normas = bloque_data['normas']

                for token in query_tokens:
                    if token in dict(diccionario):  # Verificar si el token está en el bloque
                        posting_list = dict(diccionario)[token]  # Lista de documentos y TFs
                        df = len(posting_list)  # Document Frequency (DF)

                        # Calcular TF-IDF del token en la query
                        query_tf_idf = self.compute_tf_idf(query_tf[token], df)

                        # Actualizar scores para cada documento en la posting list
                        for doc_id, tf in posting_list:
                            doc_tf_idf = self.compute_tf_idf(tf, df)
                            score = query_tf_idf * doc_tf_idf  # Producto punto parcial

                            # Actualizar el heap para top-k
                            heapq.heappush(top_k_heap, (doc_id, score))
                            if len(top_k_heap) > k:
                                heapq.heappop(top_k_heap)

        # 5. Combinar resultados y normalizar
        final_scores = {}
        for doc_id, score in top_k_heap:
            norm_query = math.sqrt(sum((self.compute_tf_idf(query_tf[token], len(dict(diccionario)[token])) ** 2) 
                                       for token in query_tokens if token in dict(diccionario)))
            
            norm_doc = bloque_normas.get(str(doc_id), 1)
            cosine_similarity = score / (norm_query * norm_doc)
            final_scores[doc_id] = cosine_similarity

        return final_scores #scores de los documentos relevantes 

    def get_relevant_blocks(self, query_tokens):
        bloque_files = [os.path.join(self.pathTemp, f) for f in os.listdir(self.pathTemp) if f.endswith('.json')]
        relevant_blocks = []
        for bloque_file in bloque_files:
            with open(bloque_file, 'r', encoding='utf-8') as f:
                bloque_data = json.load(f)
                diccionario = dict(bloque_data['diccionario'])
                if any(token in diccionario for token in query_tokens):
                    relevant_blocks.append(bloque_file)

        print("relevant blocks: ", relevant_blocks)
        return relevant_blocks   

    def get_docs(self, indexes):  #Retornar lineas especificas del csv
        result = []
        with open(self.csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)  # Leer como diccionario
            for i, row in enumerate(csv_reader): #Leo linea por linea (para no cargar todo el csv a RAM)
                if i in indexes:  
                    result.append(row)  
        return result

    def busqueda_topK(self, query, k=5): 
        start_time = time.perf_counter()

        scores = self.similitudCoseno(query, k)
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_k_results = sorted_scores[:k]
        print("top k results: ", top_k_results)
        
        doc_ids, similitud = zip(*top_k_results) #lista de ids de documento, lista de similitudes

        docs = self.get_docs(doc_ids) #diccionarios de cada uno de los documentos top k
        results = []
        for i, doc in enumerate(docs):
            result = {
                'track_id': doc['track_id'],
                'track_name': doc['track_name'],
                'track_artist': doc['track_artist'],
                'lyrics': doc['lyrics'][:10],
                'row_position': doc_ids[i]+2, 
                'similitudCoseno': similitud[i]
            }
            results.append(result)

        end_time = time.perf_counter()

        return {
            'query_time': end_time - start_time,
            'results': results
        }


# Uso
spimi = SPIMI(csv_path='./backend/data/spotify_songs_100.csv')

# Busqueda
query = 'hello enough'
result = spimi.busqueda_topK(query, k=5)
print(result)
