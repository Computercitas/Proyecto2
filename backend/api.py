from flask import Flask, request, jsonify
from spimi import SPIMI

app = Flask(__name__)

# Inicializa el índice SPIMI
path = '../data/spotify_songs.csv'
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