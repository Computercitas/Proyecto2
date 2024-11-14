import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

// Define las interfaces para los diferentes tipos de resultados
interface SPIMIResult {
  track_id: string;
  track_name: string;
  track_artist: string;
  lyrics: string;
  row_position: number;
  similitudCoseno: number;
}

interface PostgresResult {
  track_id: string;
  track_name: string;
  track_artist: string;
  lyrics: string;
  score: number;  // El campo score se usa en resultados de PostgreSQL
  rank: number;
}

// Tipo unión para manejar ambos tipos de resultados
type QueryResult = SPIMIResult | PostgresResult;

interface ApiResponse {
  results?: QueryResult[];
  error?: string;
  query_time?: number;
}

const Consulta: React.FC = () => {
  const [query, setQuery] = useState<string>("");
  const [topK, setTopK] = useState<number>(10);
  const [indexMethod, setIndexMethod] = useState<string>("SPIMI");
  const [results, setResults] = useState<QueryResult[]>([]);
  const [queryTime, setQueryTime] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const navigate = useNavigate();

  const handleQueryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  };

  const handleTopKChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTopK(Number(event.target.value));
  };

  const handleIndexMethodChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setIndexMethod(event.target.value);
  };

  const getEndpoint = (method: string) => {
    switch (method) {
      case "SPIMI":
        return "http://127.0.0.1:5000/search/spimi";
      case "PostgreSQL":
        return "http://127.0.0.1:5000/search/postgres";
      default:
        return "http://127.0.0.1:5000/search/spimi";
    }
  };

  // Función para normalizar los resultados
  const normalizeResult = (result: QueryResult): SPIMIResult => {
    if ('similitudCoseno' in result) {
      // Resultado SPIMI
      return result as SPIMIResult;
    } else {
      // Resultado PostgreSQL
      const postgresResult = result as PostgresResult;
      return {
        track_id: postgresResult.track_id,
        track_name: postgresResult.track_name,
        track_artist: postgresResult.track_artist,
        lyrics: postgresResult.lyrics,
        row_position: postgresResult.rank,
        similitudCoseno: postgresResult.score // Mapear el score a similitudCoseno
      };
    }
  };

  const handleSubmit = async () => {
    if (!query.trim()) {
      setError("Por favor, ingresa una consulta");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const startTime = performance.now();
      const endpoint = getEndpoint(indexMethod);

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query, k: topK }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Error en la consulta: ${errorText}`);
      }

      const data = await response.json();
      const endTime = performance.now();

      console.log('Respuesta del servidor:', data);

      if (data.error) {
        throw new Error(data.error);
      }

      let processedResults: QueryResult[];
      if (Array.isArray(data)) {
        processedResults = data;
      } else if (data.results) {
        processedResults = data.results;
      } else {
        processedResults = [];
      }

      setResults(processedResults.map(normalizeResult));  // Normalizar todos los resultados
      setQueryTime(data.query_time || (endTime - startTime));
      setError(null);
    } catch (error: unknown) {
      console.error("Error al realizar la consulta:", error);
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Hubo un problema con la consulta. Inténtalo de nuevo.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewDetails = (result: QueryResult) => {
    navigate(`/details/${result.track_id}`, { state: { result } });
  };

  return (
    <div className="consulta-container p-4">
      <h2 className="text-2xl font-bold mb-4">Realiza tu consulta</h2>

      <div className="mb-4">
        <label className="block mb-2">Consulta:</label>
        <input
          type="text"
          value={query}
          onChange={handleQueryChange}
          placeholder="Ingresa tu consulta"
          className="w-full p-2 border rounded"
        />
      </div>

      <div className="mb-4">
        <label className="block mb-2">Cantidad de resultados (Top K):</label>
        <input
          type="number"
          value={topK}
          onChange={handleTopKChange}
          min={1}
          max={1000}
          className="w-full p-2 border rounded"
        />
      </div>

      <div className="mb-4">
        <label className="block mb-2">Método de indexación:</label>
        <select
          value={indexMethod}
          onChange={handleIndexMethodChange}
          className="w-full p-2 border rounded"
        >
          <option value="SPIMI">SPIMI</option>
          <option value="PostgreSQL">PostgreSQL</option>
        </select>
      </div>

      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
      >
        {isLoading ? "Buscando..." : "Buscar"}
      </button>

      {error && <p className="text-red-500 mt-4">{error}</p>}

      {results.length > 0 && (
        <div className="results mt-8">
          <h3 className="text-xl font-bold mb-2">Resultados</h3>
          <p className="mb-4">Tiempo de consulta: {queryTime.toFixed(2)} milisegundos</p>
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse border">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border p-2">Acciones</th>
                  <th className="border p-2">Track ID</th>
                  <th className="border p-2">Track Name</th>
                  <th className="border p-2">Track Artist</th>
                  <th className="border p-2">Lyrics</th>
                  <th className="border p-2">Posición</th>
                  <th className="border p-2">Similitud</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result, index) => {
                  const normalizedResult = normalizeResult(result);
                  return (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="border p-2">
                        <button
                          onClick={() => handleViewDetails(result)}
                          className="bg-green-500 text-white px-2 py-1 rounded hover:bg-green-600"
                        >
                          Ver
                        </button>
                      </td>
                      <td className="border p-2">{normalizedResult.track_id ? `${normalizedResult.track_id.substring(0, 10)}...` : 'N/A'}</td>
                      <td className="border p-2">{normalizedResult.track_name ? (normalizedResult.track_name.length > 15 ? `${normalizedResult.track_name.substring(0, 15)}...` : normalizedResult.track_name) : 'N/A'}</td>
                      <td className="border p-2">{normalizedResult.track_artist ? (normalizedResult.track_artist.length > 15 ? `${normalizedResult.track_artist.substring(0, 15)}...` : normalizedResult.track_artist) : 'N/A'}</td>
                      <td className="border p-2">{normalizedResult.lyrics ? (normalizedResult.lyrics.length > 25 ? `${normalizedResult.lyrics.substring(0, 25)}...` : normalizedResult.lyrics) : 'N/A'}</td>
                      <td className="border p-2">{normalizedResult.row_position}</td>
                      <td className="border p-2">{normalizedResult.similitudCoseno?.toFixed(2) ?? 'NA'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Consulta;