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

nltk.download('punkt_tab') #Tokenizador
nltk.download('stopwords')

class SPIMI:
    def __init__(self, csv_path, pathTemp='indice'):
        self.csv_path = csv_path
        self.mb_per_block = 4 * 1024            # MBs por bloque 
        self.total_docs = self.count_csv_rows() # Total de documentos (filas)
        self.pathTemp = pathTemp                # Path para guardar los bloques/índices/hacer merge
        self.stop_words = set(stopwords.words('spanish')).union(set(stopwords.words('english'))) 
        self.stemmer = SnowballStemmer('english')
        self.build_time = 0  # Para medir el tiempo de construcción del índice
        self.normas_docs = {}
        if not os.path.exists(self.pathTemp): #Verifico si ya tengo una carpeta con índices
            os.makedirs(self.pathTemp)
            self.construirSpimi(self.mb_per_block)
            self.merge()
            print("Tiempo de construcción del índice para ", self.total_docs, " documentos: ", round(self.build_time, 2)*1000, "ms")
        else: 
            print("Reutilizando índice para ", csv_path, " con ", self.total_docs, " filas")
            #Borrar la carpeta indice si es que quieres probar con un csv diferente, para que se genere el índice denuevo

    def count_csv_rows(self): #Calcular total de documentos (sin cargar todo el csv en la RAM)
        with open(self.csv_path, 'r', encoding='utf-8') as file:
            return sum(1 for _ in file) - 1 #-1 por el header

    def preProcesamiento(self, texto):
        if isinstance(texto, float): # Caso NaN
            return [] 
        
        # Quitar puntuación y términos que no son ascii
        texto = re.sub(r'[^\x00-\x7F]+', '', texto) 
        texto = re.sub(r'[^\w\s]', '', texto)
        tokens = word_tokenize(texto.lower())

        """
        Aqui aplicamos el stemmer solamente en ingles. Hicimos una condicional para identificar el idioma
        de cada palabra y en base a eso aplicar el stemming en español o inglés, pero la generación de bloques
        tardaba MUCHO más. Así que dejamos solamente stemming en inglés y quitamos stopwords en inglés y español.
        (Casi el 90% de las canciones están en inglés)
        """
        tokens = [self.stemmer.stem(word) for word in tokens if word not in self.stop_words and word.isalpha()]
        return tokens

    def construirSpimi(self, limite_mb_bloque): 
        start_time = time.perf_counter() # Medir tiempo de construcción
        block_number = 0
        start_line = 0
        
        """
        Voy a generar bloques con los índices invertidos y las normas. Los bloques tienen una capacidad límite que 
        verifico si ya he alcanzado cada vez que proceso un documento (letra de una canción). Mantengo contadores
        para saber donde en que línea me he quedado en el csv una vez que se llena un bloque y para saber el número
        del archivo del bloque (bloque_0, bloque_1, ...)
        """

        while True:  # Creo bloques hasta leer todo el csv
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
        self.build_time = end_time - start_time # Le voy a sumar el merge a esto, ya que es parte de la construcción

    def merge(self):
        bloque_files = [os.path.join(self.pathTemp, f) for f in os.listdir(self.pathTemp) if f.endswith('.json')]
        term_files = {}
        normas = defaultdict(float)

        for bloque_file in bloque_files:
            with open(bloque_file, 'r', encoding='utf-8') as f:
                bloque_data = json.load(f)
                diccionario = bloque_data['diccionario']
                bloque_normas = bloque_data['normas']

                for term, postings in diccionario.items():
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
        sorted_terms = sorted(term_postings.keys())
        num_bloques = len(bloque_files)
        terms_per_block = len(sorted_terms) // num_bloques + 1

        for bloque_id in range(num_bloques):
            start_idx = bloque_id * terms_per_block
            end_idx = min((bloque_id + 1) * terms_per_block, len(sorted_terms))
            block_terms = sorted_terms[start_idx:end_idx]
            block_postings = {term: term_postings[term] for term in block_terms}

            final_block = {
                'diccionario': block_postings,
                'normas': normas
            }
            block_file = os.path.join(self.pathTemp, f'index_bloque_{bloque_id}.json')
            with open(block_file, 'w', encoding='utf-8') as f:
                json.dump(final_block, f, ensure_ascii=False)
            
            os.remove(os.path.join(self.pathTemp, f'bloque_{bloque_id}.json')) # Remover block files originales

        for term_file in term_files.values():
            os.remove(term_file)
    
    def compute_tf_idf(self, tf, df):
        return tf * math.log10(self.total_docs / (df + 1))  # +1 para no dividir por cero
    
    def similitudCoseno(self, query, k):
        # 1. Preprocesar la query
        query_tokens = self.preProcesamiento(query)

        # 2. Identificar bloques relevantes (que contienen términos de la query)
        bloques_relevantes = self.get_relevant_blocks(query_tokens)

        # 3. Buscar los índices asociados a cada palabra de la query
        posting_lists = {} # Con esto vamos a revisar todos los docs que contienen las palabras de la query para ver el más similar
        for token in query_tokens:
            for bloque in bloques_relevantes:  # itero solo sobre bloques relevantes
                with open(bloque, 'r', encoding='utf-8') as f:
                    bloque_data = json.load(f)
                    diccionario = dict(bloque_data['diccionario']) # Cargar las palabras del bloque a un diccionario
                    if token in diccionario:  # si el token está en el diccionario (solo de ese bloque)
                        if token not in posting_lists: 
                            posting_lists[token] = []
                        posting_lists[token].extend(diccionario[token]) # Esto es para casos donde tengo una palabra más de una vez en query

        # 4. Calcular TF-IDF
        # 4.1 TF-IDF para la query
        tf_idf_query = {}
        query_tf = Counter(query_tokens)  
        for token, tf in query_tf.items():
            if token in posting_lists: 
                df = len(posting_lists[token])  
                tf_idf_query[token] = self.compute_tf_idf(tf, df) 
            else:
                tf_idf_query[token] = 0  

        # 4.2 TF-IDF para los documentos relevantes que encontramos
        tf_idf_docs = defaultdict(float)
        for token, postings in posting_lists.items():
            for doc_id, tf in postings:
                df = len(postings)  
                tf_idf_docs[doc_id] += self.compute_tf_idf(tf, df) * tf_idf_query[token]  

        # 5. Normalización y similitud <----- ARREGLAR!!
        final_scores = {}
        norm_query = math.sqrt(sum(tf_idf_query[token] ** 2 for token in query_tokens if tf_idf_query[token] > 0))  
        for doc_id, score in tf_idf_docs.items():
            if doc_id in self.normas_docs:  
                norm_doc = math.sqrt(self.normas_docs[doc_id]) 
                cosine_similarity = score / (norm_query * norm_doc) if norm_query * norm_doc > 0 else 0
                final_scores[doc_id] = cosine_similarity
            else:
                print(f"Warning: Document {doc_id} missing in normas_docs.") #Puse este warning pk no se que hacer xd

        # 6. Ordenar y devolver los top-k resultados
        top_k = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return top_k

    def get_relevant_blocks(self, query_tokens): # Itero sobre cada bloque para ver si contiene palabras de la query
        bloque_files = [os.path.join(self.pathTemp, f) for f in os.listdir(self.pathTemp) if f.endswith('.json')]
        relevant_blocks = []
        for bloque_file in bloque_files: # Para cada archivo dentro de la carpeta donde están los bloques
            with open(bloque_file, 'r', encoding='utf-8') as f:
                bloque_data = json.load(f)
                diccionario = dict(bloque_data['diccionario']) # Traigo los índices de ese bloque
                if any(token in diccionario for token in query_tokens):
                    relevant_blocks.append(bloque_file)

        print("relevant blocks: ", relevant_blocks)
        return relevant_blocks   

    def get_docs(self, indexes):  # Retornar líneas específicas del CSV
        result = []
        with open(self.csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)  # Leer como diccionario
            header_offset = 2  # Ajustar offset (header + 1)
            for i, row in enumerate(csv_reader, start=header_offset): 
                if i in indexes:
                    result.append(row)
        return result


    def busqueda_topK(self, query, k=5): 
        start_time = time.perf_counter() # Para calcular tiempo de búsqueda

        scores = self.similitudCoseno(query, k)

        # Por alguna razón mi top_k está saliendo vacio, creo que es por la normalización y similitud (similitudCoseno())


        top_k_results = sorted(scores, key=lambda score: score[1], reverse=True)
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
#Si la carpeta indice no existe se van a generar los índices. Caso contrario reutiliza los índices existentes

# Busqueda
query = 'hello always'
result = spimi.busqueda_topK(query, k=5)
print(result)