import React from "react";
import { Link } from "react-router-dom";  // Para usar rutas de navegación

const Home: React.FC = () => {
  return (
    <div className="home-container">
      <h1>¡Bienvenidos!</h1>
      <p>Esta es una página para probar el índice invertido con un dataset de Spotify. Puedes realizar consultas tipo SQL y obtener resultados de forma eficiente.</p>
      <div className="button-container">
        <Link to="/consulta">
          <button className="consulta-button">Consulta!</button>
        </Link>
        <a href="https://github.com/Dateadores/Proyecto2" target="_blank" rel="noopener noreferrer">
          <button className="github-button">Github</button>
        </a>
      </div>
    </div>
  );
};

export default Home;
