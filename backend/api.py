from flask import Flask, request, jsonify
from spimi import SPIMI

app = Flask(__name__)

# Inicializa el índice SPIMI
path = './backend/data/spotify_songs.csv'
spimi = SPIMI(csv_path=path)

@app.route('/search', methods=['GET'])
def search_get():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    k = int(request.args.get('k', 5))
    results = spimi.busqueda_topK(query, k)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)


#Como correr la api
# 1. Instalar flask y correr el archivo api.py para inicializar
#   si el índice no está creado, al correr el archivo se va a crear (1 min aprox)
#   si ya esta creado apenas llamará al indice ya existente 
#

# 2. hacer click en la dirección que sale en consola
# 3. probar api en la ruta /search, con la consulta que quiera, ejemplo http://127.0.0.1:5000/search?query=love&k=5
# tambien se puede probar con strings de texto tipo http://127.0.0.1:5000/search?query="i like turtles"&k=5
# tambien puedes cambiar el valor de k (cuantos elementos retorna la consulta)