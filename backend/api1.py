from flask import Flask, request, jsonify
from flask_cors import CORS
from spimi import SPIMI
from postgres import PostgresConnector
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permitir CORS para solicitudes desde cualquier origen

# Inicializa el índice SPIMI
path = './backend/data/spotify_songs.csv'
spimi = SPIMI(csv_path=path)

# Inicializar PostgreSQL
db = PostgresConnector()
db.setup_database()

# Endpoints para SPIMI
@app.route('/search/spimi', methods=['POST'])
def search_spimi():
    try:
        data = request.get_json()
        query = data.get('query')
        k = int(data.get('k', 5))

        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400

        results = spimi.busqueda_topK(query, k)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error en búsqueda SPIMI: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoints para PostgreSQL
@app.route('/search/postgres', methods=['POST'])
def search_postgres():
    try:
        data = request.get_json()
        query = data.get('query')
        k = int(data.get('k', 5))

        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400

        results = db.search(query, k)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error en búsqueda PostgreSQL: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/search/postgres/lyrics', methods=['POST'])
def search_postgres_lyrics():
    try:
        data = request.get_json()
        lyrics = data.get('lyrics')
        k = int(data.get('k', 5))

        if not lyrics:
            return jsonify({'error': 'Lyrics parameter is required'}), 400

        results = db.search_lyrics(lyrics, k)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error en búsqueda de letras PostgreSQL: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
