import os
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
import json  # Para almacenar bloques en disco

nltk.download('stopwords')

class Bloque:
    """
    Bloque: Esta estuctura va a contener el índice invertido, pero no todo el índice invertido, sino solo una parte.
    Lo que se hace es que se va a guardar en disco cada vez que se llene la memoria. (Esa es la idea)

    """
    def __init__(self, path, bloque_id):
        # Directorio donde se guardará el bloque
        self.path = path
        # ID del bloque
        self.bloque_id = bloque_id               
        # Índice invertido del bloque   
        self.indice_invertido = defaultdict(list)
        # Contador de documentos en el bloque
        self.doc_count = 0                          
    
    # Permite agregar un término al índice invertido del bloque
    def agregar_termino(self, termino, doc_id):
        if doc_id not in self.indice_invertido[termino]:
            self.indice_invertido[termino].append(doc_id)
    
    # Se guarda el boque en disco en formato JSON
    def guardar_en_disco(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        with open(f"{self.path}/bloque_{self.bloque_id}.json", 'w') as f:
            json.dump(self.indice_invertido, f)
        # Limpiar el índice invertido después de guardarlo
        self.indice_invertido = defaultdict(list)

class SPIMI:
    def __init__(self, csv_path, output_path, memoria_maxima=1000):
        self.csv_path = csv_path
        self.output_path = output_path
        self.memoria_maxima = memoria_maxima  # Máximo número de documentos en memoria
        self.bloques = []
        self.doc_id = 0
        self.bloque_actual = Bloque(output_path, len(self.bloques))
        self.stop_words = set(stopwords.words('spanish'))
        self.stemmer = SnowballStemmer('spanish')
        # self.stop_words = set(stopwords.words('english'))
        # self.stemmer = SnowballStemmer('english')

        """ 
        Pasa algo curioso a tener en cuenta, cuando uso spanish, trato de buscar la palabra "everybody" si la en cuentra:
        "everybody": [5, 8, 19, 73, 83, 97]
        pero en ingls, 
        la tiene pero como #everybodi"
        """

    # Leer archivo CSV en trozos para evitar cargar todo en memoria
    def cargar_archivo(self):
        return pd.read_csv(self.csv_path, chunksize=1000)

    def preprocesar(self, texto):
        # Convierte a minúsculas, tokeniza, remueve stopwords, aplica stemming
        # Quiza falte un poco más de preprocesamiento (!)
        tokens = word_tokenize(texto.lower())
        tokens = [self.stemmer.stem(word) for word in tokens if word not in self.stop_words and word.isalpha()]
        return tokens

    def scoreTF(self, tf):
        # Calcula el score TF (Frecuencia de término)
        return np.log10(tf) + 1 if tf > 0 else 0

    def scoreIDF(self, N, df):
        # Calcula el score IDF (Inversa de la Frecuencia en Documentos)
        return np.log10(N / (1 + df))

    def construir_spimi(self):
        # Procesar el archivo en chunks y construir el índice invertido usando SPIMI
        for chunk in self.cargar_archivo():
            for _, fila in chunk.iterrows():
                self.doc_id += 1
                texto = fila['lyrics']  # Uso la columna 'lyrics'
                tokens = self.preprocesar(texto)

                for token in tokens:
                    self.bloque_actual.agregar_termino(token, self.doc_id)

                # Límite de memoria alcanzado
                if self.doc_id % self.memoria_maxima == 0:
                    self.bloques.append(self.bloque_actual)
                    self.bloque_actual.guardar_en_disco()  # Guardar el bloque en memoria secundaria
                    self.bloque_actual = Bloque(self.output_path, len(self.bloques))

        # Guardar cualquier bloque restante
        if self.bloque_actual.indice_invertido:
            self.bloque_actual.guardar_en_disco()
            self.bloques.append(self.bloque_actual)

    def merge(self):
        # Combina todos los bloques generados en disco en un índice invertido final
        indice_final = defaultdict(list)
        for i in range(len(self.bloques)):
            with open(f"{self.output_path}/bloque_{i}.json", 'r') as f:
                bloque_data = json.load(f)
                for termino, doc_list in bloque_data.items():
                    if termino in indice_final:
                        indice_final[termino].extend(doc_list)
                    else:
                        indice_final[termino] = doc_list

        # Guardar índice final
        with open(f"{self.output_path}/indice_final.json", 'w') as f:
            json.dump(indice_final, f)

    def buscar(self, termino):
        # Realiza una búsqueda en el índice invertido final
        pass

# Uso
spimi = SPIMI(csv_path='./data/spotify_songs_100.csv', output_path='indice')
spimi.construir_spimi()
spimi.merge()

