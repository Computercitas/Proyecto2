from flask import Flask, request, jsonify
from flask_cors import CORS
from spimi import SPIMI

app = Flask(__name__)
CORS(app)  # Permitir CORS para solicitudes desde cualquier origen

# Inicializa el índice SPIMI
path = './backend/data/spotify_songs.csv'
spimi = SPIMI(csv_path=path)

@app.route('/search', methods=['POST'])
def search_post():
    data = request.get_json()  # Obtén los datos del cuerpo de la solicitud
    query = data.get('query')
    k = int(data.get('k', 5))

    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    results = spimi.busqueda_topK(query, k)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)