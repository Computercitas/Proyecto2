import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

// Definición de la interfaz para los detalles de la canción
interface TrackDetails {
  track_name: string;
  track_artist: string;
  lyrics: string;
  similitudCoseno?: number;
  similitud?: number;
  row_position: number;
}

const Detalle: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Obtener los detalles de la canción desde el estado
  const { trackDetails, similitud } = location.state || {};

  // Asegurarse de que trackDetails tiene el tipo correcto
  const details = trackDetails as TrackDetails;

  // Si no se encuentran detalles, mostrar un mensaje
  if (!details) {
    return <p>No se encontraron detalles de la canción.</p>;
  }  

  return (
    <div className="detalle-cancion">
      <h2>Detalles de la Canción</h2>
      <p><strong>Nombre de la Canción:</strong> {details.track_name}</p>
      <p><strong>Artista:</strong> {details.track_artist}</p>
      
      {/* Agregar un contenedor con scroll para las letras */}
      <div className="lyrics-container" style={{ maxHeight: '200px', overflowY: 'auto' }}>
        <p><strong>Letras:</strong> {details.lyrics}</p>
      </div>

      <p><strong>Similitud Coseno:</strong> {similitud}</p> {/* Mostrar similitud correctamente */}
      <p><strong>Posición de Fila:</strong> {details.row_position}</p>
      
      {/* Botón para volver a la página anterior */}
      <button onClick={() => navigate('/consulta')}>Volver</button>
    </div>
  );
};

export default Detalle;
