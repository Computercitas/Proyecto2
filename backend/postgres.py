import psycopg2 as pg
import pandas as pd
from psycopg2.extras import RealDictCursor
import time

class PostgresConnector:
    def __init__(self):
        self.connection_params = {
            "user": "postgres",
            "password": "Ut3c-4536",
            "host": "localhost",
            "port": "5433",
            "database": "ProyectoFinalBD2"
        }
        self.connect()
        
    def connect(self):
        self.conn = pg.connect(**self.connection_params)
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
    def setup_database(self):
        # Crear schema si no existe
        self.cur.execute("CREATE SCHEMA IF NOT EXISTS db2;")
        
        # Crear tabla
        create_table_query = """
        CREATE TABLE IF NOT EXISTS db2.spotify_songs (
            track_id VARCHAR PRIMARY KEY,
            track_name VARCHAR,
            track_artist VARCHAR,
            lyrics TEXT,
            search_vector tsvector
        );
        """
        self.cur.execute(create_table_query)
        
        # Crear índice GIN
        self.cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_songs_search 
        ON db2.spotify_songs USING gin(search_vector);
        """)
        
        # Crear función de actualización del vector
        self.cur.execute("""
        CREATE OR REPLACE FUNCTION db2.update_search_vector()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector = 
                setweight(to_tsvector('english', COALESCE(NEW.track_name,'')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.track_artist,'')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.lyrics,'')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        # Crear trigger
        self.cur.execute("""
        DROP TRIGGER IF EXISTS trigger_search_vector ON db2.spotify_songs;
        CREATE TRIGGER trigger_search_vector
        BEFORE INSERT OR UPDATE ON db2.spotify_songs
        FOR EACH ROW
        EXECUTE FUNCTION db2.update_search_vector();
        """)
        
        self.conn.commit()

    def load_data(self, csv_path):
        # Verificar si ya hay datos
        self.cur.execute("SELECT COUNT(*) FROM db2.spotify_songs")
        if self.cur.fetchone()['count'] > 0:
            print("Los datos ya están cargados")
            return
            
        # Cargar datos desde CSV
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            self.cur.execute("""
            INSERT INTO db2.spotify_songs (track_id, track_name, track_artist, lyrics)
            VALUES (%s, %s, %s, %s)
            """, (row['track_id'], row['track_name'], row['track_artist'], row['lyrics']))
        
        self.conn.commit()

    def search(self, query, k=5):
        start_time = time.time()
        
        search_query = """
        SELECT 
            track_id,
            track_name,
            track_artist,
            lyrics,
            ctid::text as row_position,
            ts_rank_cd(search_vector, plainto_tsquery('english', %s)) as similitud
        FROM db2.spotify_songs
        WHERE search_vector @@ plainto_tsquery('english', %s)
        ORDER BY similitud DESC
        LIMIT %s;
        """
        
        self.cur.execute(search_query, (query, query, k))
        results = self.cur.fetchall()
        
        return {
            'query_time': time.time() - start_time,
            'results': results
        }
  
    def search_lyrics(self, lyrics_fragment, k=5):
        start_time = time.time()
        
        search_query = """
        SELECT 
            track_id,
            track_name,
            track_artist,
            lyrics,
            ctid::text as row_position,
            ts_rank_cd(to_tsvector('english', lyrics), 
                      plainto_tsquery('english', %s)) as similitud
        FROM db2.spotify_songs
        WHERE 
            lyrics ILIKE %s 
            OR lyrics @@ plainto_tsquery('english', %s)
        ORDER BY similitud DESC
        LIMIT %s;
        """
        
        # Usar %% para escapar el % en ILIKE
        lyrics_pattern = f'%{lyrics_fragment}%'
        
        self.cur.execute(search_query, 
                        (lyrics_fragment, lyrics_pattern, lyrics_fragment, k))
        results = self.cur.fetchall()
        
        return {
            'query_time': time.time() - start_time,
            'results': results
        }

    def __del__(self):
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'conn'):
            self.conn.close()

# Uso

# db = PostgresConnector()
# db.setup_database()
# db.load_data('../data/spotify_songs.csv')

# # Búsqueda
# results = db.search('love', 10)
# for result in results['results']:
#     print(f"Canción: {result['track_name']}")
#     print(f"Artista: {result['track_artist']}")
#     print(f"Similitud: {result['similitud']}")
#     print("---")

# Ejemplo de uso:
"""
# Buscar fragmento de letra
results = db.search_lyrics("Two kids with their hearts on fire Who's gonna save us now? When we thought", 10)
for result in results['results']:
		print(f"ID de la canción: {result['track_id']}")
		print(f"Nombre de la canción: {result['track_name']}")
		print(f"Artista: {result['track_artist']}")
		# print(f"Letras: {result['lyrics']}")
		print(f"Posición de la fila: {result['row_position']}")
		print(f"Similitud: {result['similitud']}")
		print("---")
"""

