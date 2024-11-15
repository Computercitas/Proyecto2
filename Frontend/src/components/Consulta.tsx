import React, { useState } from 'react';
import './Consulta.css';

interface Resultado {
  track_name: string;
  track_artist: string;
  lyrics: string;
  similitudCoseno?: number;
  similitud?: number;
  row_position: number;
}

const Consulta: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [k, setK] = useState<number>(5);
  const [resultados, setResultados] = useState<Resultado[]>([]);
  const [expandedTrack, setExpandedTrack] = useState<Resultado | null>(null);
  const [searchExecuted, setSearchExecuted] = useState<boolean>(false); // Estado para saber si se ha hecho una búsqueda

  const mostrarResultados = (data: { results: Resultado[] }) => {
    setResultados(data.results);
    setSearchExecuted(true); // Marcar que se ha ejecutado una búsqueda
  };

  const obtenerValorK = () => {
    return k ? parseInt(k.toString()) : 5;
  };

  const searchSPIMI = () => {
    fetch('http://localhost:5000/search/spimi', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, k: obtenerValorK() }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        mostrarResultados(data);
      })
      .catch((error) => console.error('Error en búsqueda SPIMI:', error));
  };

  const searchPostgres = () => {
    fetch('http://localhost:5000/search/postgres', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, k: obtenerValorK() }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        mostrarResultados(data);
      })
      .catch((error) => console.error('Error en búsqueda PostgreSQL:', error));
  };

  const recortarLyrics = (lyrics: string) => {
    const palabras = lyrics.split(' ');
    if (palabras.length > 5) {
      return palabras.slice(0, 5).join(' ') + '...';
    }
    return lyrics;
  };

  const verDetalle = (resultado: Resultado) => {
    setExpandedTrack(resultado);
  };

  const cerrarDetalle = () => {
    setExpandedTrack(null);
  };

  return (
    <div className="Consulta">
      <h1>¡Make your enquiry!</h1>
      <div>
        <label htmlFor="query">Enter your query:</label>
        <input
          type="text"
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="k">Enter the value of k:</label>
        <input
          type="number"
          id="k"
          value={k}
          min="1"
          onChange={(e) => setK(Number(e.target.value))}
        />
      </div>
      <div className="botones-container">
        <button onClick={searchSPIMI}>SPIMI</button>
        <button onClick={searchPostgres}>PostgreSQL</button>
      </div>

      <div id="resultados">
        {searchExecuted && resultados.length === 0 && (
          <p>No results found.</p>
        )}
        {resultados.length > 0 && (
          <div className="resultados-container">
            <table className="resultados-table">
              <thead>
                <tr>
                  <th>Track Name</th>
                  <th>Artist</th>
                  <th>Lyrics</th>
                  <th>Similitud</th>
                  <th>Row Position</th>
                  <th>Detail</th>
                </tr>
              </thead>
              <tbody>
                {resultados.map((resultado, index) => (
                  <tr key={index} className="resultado-row">
                    <td>{resultado.track_name}</td>
                    <td>{resultado.track_artist}</td>
                    <td>{recortarLyrics(resultado.lyrics)}</td>
                    <td>{resultado.similitudCoseno || resultado.similitud}</td>
                    <td>{resultado.row_position}</td>
                    <td>
                      <button onClick={() => verDetalle(resultado)}>Ver</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {expandedTrack && (
          <div className="detalle-cancion">
            <h2>Detalles de la Canción</h2>
            <p><strong>Track Name:</strong> {expandedTrack.track_name}</p>
            <p><strong>Artist:</strong> {expandedTrack.track_artist}</p>
            <div className="lyrics-scroll">
              <p><strong>Lyrics:</strong> {expandedTrack.lyrics}</p>
            </div>
            <p><strong>Similitud Coseno:</strong> {expandedTrack.similitudCoseno || expandedTrack.similitud}</p>
            <p><strong>Row Position:</strong> {expandedTrack.row_position}</p>
            <button onClick={cerrarDetalle}>Cerrar</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Consulta;
