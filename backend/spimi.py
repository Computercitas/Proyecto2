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
    def __init__(self, csv_path, pathTemp='indice'):
        self.csv_path = csv_path
        self.mb_per_block = 4 * 1024 * 1024 #4MB
        self.total_docs = self.count_csv_rows()
        self.pathTemp = pathTemp
        self.stop_words = set(stopwords.words('spanish')).union(set(stopwords.words('english')))
        self.stemmer = SnowballStemmer('english')
        self.build_time = 0  # Para medir el tiempo de construcción del índice

        if not os.path.exists(self.pathTemp):
            os.makedirs(self.pathTemp)
            self.construirSpimi(self.mb_per_block)
            self.merge()
            #self.eliminarIdx_n() 
            print("Tiempo de construcción del índice para ", self.total_docs, " documentos: ", round(self.build_time, 2)*1000, "ms")
        else: 
            print("Reutilizando índice para ", csv_path, " con ", self.total_docs, " filas")
            #Borrar la carpeta indice si es que quieres probar con un csv diferente, para que se genere el índice denuevo

    def count_csv_rows(self): #Calcular total de documentos (sin cargar todo el csv en la RAM)
        with open(self.csv_path, 'r', encoding='utf-8') as file:
            return sum(1 for _ in file) - 1 #-1 por el header

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

    def merge(self): #TODO: Hacer merge en memoria secundaria, sin traer todo a la RAM
        start_time = time.perf_counter() 

        all_tokens = defaultdict(list)  
        combined_norms = defaultdict(float)  

        bloque_files = [os.path.join(self.pathTemp, f) for f in os.listdir(self.pathTemp) if f.endswith('.json')]

        for bloque_file in bloque_files:
            with open(bloque_file, 'r', encoding='utf-8') as f:
                bloque_data = json.load(f)
                diccionario = bloque_data['diccionario']
                bloque_normas = bloque_data['normas']

                for token, posting_list in dict(diccionario).items():
                    all_tokens[token].extend(posting_list)

                for doc_id, norm in bloque_normas.items():
                    combined_norms[int(doc_id)] += norm

        sorted_tokens = sorted(all_tokens.items())  

        block_ranges = {}  
        block_size = 1000  
        current_block = []
        current_block_norms = defaultdict(float)
        block_index = 0

        for token, posting_list in sorted_tokens:
            current_block.append((token, posting_list))
            for doc_id, _ in posting_list:
                current_block_norms[doc_id] = combined_norms[doc_id]

            if len(current_block) >= block_size:
                block_file = os.path.join(self.pathTemp, f'bloque_{block_index}.json')
                self.write_block(block_file, current_block, current_block_norms)
                block_ranges[block_index] = (current_block[0][0], current_block[-1][0])
                current_block = []
                current_block_norms = defaultdict(float)
                block_index += 1

        if current_block:
            block_file = os.path.join(self.pathTemp, f'bloque_{block_index}.json')
            self.write_block(block_file, current_block, current_block_norms)
            block_ranges[block_index] = (current_block[0][0], current_block[-1][0])

        end_time = time.perf_counter()
        self.build_time += (end_time - start_time) 

    def write_block(self, block_file, tokens, norms):
        sorted_block = {
            'diccionario': tokens,
            'normas': norms
        }
        with open(block_file, 'w', encoding='utf-8') as file:
            json.dump(sorted_block, file, ensure_ascii=False)
    
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

    def get_docs(self, indexes):  # Retornar líneas específicas del CSV
        result = []
        with open(self.csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)  # Leer como diccionario
            header_offset = 2  # Saltar header del csv
            for i, row in enumerate(csv_reader, start=header_offset):  # Adjust the index to account for header
                if i in indexes:
                    result.append(row)
        return result


    def busqueda_topK(self, query, k=5): 
        start_time = time.perf_counter()

        scores = self.similitudCoseno(query, k)
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_k_results = sorted_scores[:k]
        print("top k results: ", top_k_results)
        
        if len(top_k_results) == 0: 
            return f"No results for the query {query}"
        doc_ids, similitud = zip(*top_k_results) #lista de ids de documento, lista de similitudes

        docs = self.get_docs(doc_ids) #diccionarios de cada uno de los documentos top k
        results = []
        for i, doc in enumerate(docs):
            result = {
                'track_id': doc['track_id'],
                'track_name': doc['track_name'],
                'track_artist': doc['track_artist'],
                'lyrics': doc['lyrics'][:10],
                'row_position': doc_ids[i], 
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
query = 'hello as always'
result = spimi.busqueda_topK(query, k=5)
print(result)