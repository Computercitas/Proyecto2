// src/components/Consulta.tsx
import React, { useState } from "react";

// Define la interfaz para un resultado de consulta
interface QueryResult {
  title: string;
  artist: string;
  lyric: string;
}

// Simulamos una función que ejecutaría la consulta y devuelve resultados
const executeQuery = (query: string, topK: number, indexMethod: string) => {
  // Simula el tiempo de consulta (en un caso real, esto sería una llamada a un backend)
  const startTime = Date.now();
  
  // Puedes utilizar el valor de indexMethod aquí para simular qué método de indexación se usa
  console.log("Método de indexación seleccionado:", indexMethod);

  // Datos simulados (en un caso real, estos datos vendrían de una base de datos)
  const mockData: QueryResult[] = [
    { title: "Amor en tiempos de guerra", artist: "Artista 1", lyric: "Canción sobre amor en tiempos de guerra" },
    { title: "Cielo rojo", artist: "Artista 2", lyric: "Liricas que hablan del amor perdido" },
    { title: "Guerra y paz", artist: "Artista 3", lyric: "Una balada sobre la guerra y la paz" },
    { title: "La vida es bella", artist: "Artista 4", lyric: "Reflexiones sobre la vida y la guerra" },
  ];

  // Simulamos un filtro basado en la consulta
  const searchTerm = query.split("where lyric @@ '")[1]?.split("'")[0]; // Extraemos el término de búsqueda
  const filteredResults = mockData.filter(item =>
    item.lyric.toLowerCase().includes(searchTerm?.toLowerCase() || "")
  );

  const topResults = filteredResults.slice(0, topK);

  const endTime = Date.now();
  const queryTime = endTime - startTime;

  return { results: topResults, queryTime };
};

const Consulta: React.FC = () => {
  const [query, setQuery] = useState<string>("");
  const [topK, setTopK] = useState<number>(10);
  const [indexMethod, setIndexMethod] = useState<string>("Propio");
  const [results, setResults] = useState<QueryResult[]>([]);
  const [queryTime, setQueryTime] = useState<number>(0);

  const handleQueryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  };

  const handleTopKChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTopK(Number(event.target.value));
  };

  const handleIndexMethodChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setIndexMethod(event.target.value);
  };

  const handleSubmit = () => {
    // Llamamos a la función que simula la ejecución de la consulta
    const { results, queryTime } = executeQuery(query, topK, indexMethod);
    setResults(results);
    setQueryTime(queryTime);
  };

  return (
    <div className="consulta-container">
      <h2>Realiza tu consulta</h2>
      
      <div>
        <label>Consulta SQL:</label>
        <input
          type="text"
          value={query}
          onChange={handleQueryChange}
          placeholder="Ingresa tu consulta SQL"
        />
      </div>

      <div>
        <label>Cantidad de resultados (Top K):</label>
        <input
          type="number"
          value={topK}
          onChange={handleTopKChange}
          min={1}
          max={100}
        />
      </div>

      <div>
        <label>Método de indexación:</label>
        <select value={indexMethod} onChange={handleIndexMethodChange}>
          <option value="Propio">Implementación Propia</option>
          <option value="PostgreSQL">PostgreSQL</option>
        </select>
      </div>

      <button onClick={handleSubmit}>Buscar</button>

      {results.length > 0 && (
        <div className="results">
          <h3>Resultados</h3>
          <ul>
            {results.map((result, index) => (
              <li key={index}>
                <strong>{result.title}</strong> by {result.artist} - {result.lyric}
              </li>
            ))}
          </ul>
          <p>Tiempo de consulta: {queryTime} ms</p>
        </div>
      )}
    </div>
  );
};

export default Consulta;
