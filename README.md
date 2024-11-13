# Proyecto2

### Autores

- [Mariel Carolina Tovar Tolentino](https://github.com/MarielUTEC)  
- [Noemi Alejandra Huarino Anchillo](https://github.com/NoemiHuarino-utec)  
- [Sergio Sebastian Sotil Lozada](https://github.com/Sergio-So)  
- [Davi Magalhaes Eler](https://github.com/CS-DaviMagalhaes)  
- [Jose Eddison Pinedo Espinoza](https://github.com/EddisonPinedoEsp) 

## Introducción

### Objetivo

### Backend

Esta aplicación de backend está diseñada para manejar procesamiento, almacenamiento y recuperación de datos de canciones a gran escala. Incluye:

1. **Indexación Invertida Basada en SPIMI** para una recuperación eficiente de texto y cálculo de similitud de coseno.
2. **Integración con Base de Datos PostgreSQL** para almacenar metadatos de canciones y letras con un índice GIN.
3. **APIs** para realizar búsquedas y recuperar datos de canciones.

## 1. SPIMI (Single-Pass In-Memory Indexing)

La clase `SPIMI` gestiona la indexación a gran escala y la recuperación eficiente de letras de canciones utilizando un índice invertido. Incluye:

- **Carga de Datos**: Lee datos de canciones (ID de pista, nombre, artista y letras) desde un archivo CSV.
- **Preprocesamiento**: Tokeniza, elimina palabras vacías y realiza la derivación de palabras.
- **Construcción del Índice**: Divide los datos en bloques, indexa frecuencias de términos y calcula las normas de cada documento.
- **Similitud de Coseno**: Calcula la similitud entre la consulta y los documentos para devolver resultados relevantes.
- **Gestión de Archivos**: Guarda archivos de índice intermedios y los fusiona en un índice final almacenado en formato JSON.

### Ejemplo de Uso

Para inicializar y construir el índice, carga los datos desde un archivo CSV:

```python
spimi = SPIMI(csv_path='./backend/data/spotify_songs.csv')
query = 'hello'
result = spimi.busqueda_topK(query, k=5)
print(result)
```
## 2. Integración con PostgreSQL
## 3. APIs

Los archivos de API (`api.py`, `api1.py`) exponen endpoints REST para interactuar con el backend y facilitar el acceso a los datos de canciones:

- **Endpoint de Búsqueda**: Este endpoint acepta un parámetro de consulta, que permite buscar en la base de datos de canciones y recuperar los mejores resultados en función de la similitud. 
- **Endpoints Adicionales**: Proporciona funcionalidades de consulta avanzadas, como la búsqueda por fragmento de letra o por atributos específicos de la pista.


### Frontend
