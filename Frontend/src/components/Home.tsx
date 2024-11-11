import { Link } from "react-router-dom";
import { FaGithub } from "react-icons/fa"; // Ícono de GitHub
import '../App.css';
const Home = () => {
  return (
    <div className="home-container">
      <div className="content-overlay">
        <h1>Bienvenidos!</h1>
        <p>
          Esta página permite realizar consultas sobre un índice invertido
          usando un dataset de Spotify. Elige tu método de indexación y
          realiza consultas de texto libre.
        </p>
        <div className="button-container">
          <Link to="/consulta">
            <button className="consulta-button">Consulta!</button>
          </Link>
          <a href="https://github.com/Dateadores/Proyecto2" target="_blank" rel="noopener noreferrer">
            <button className="github-button">
              <FaGithub size={20} /> GitHub
            </button>
          </a>
        </div>
      </div>
    </div>
  );
};

export default Home;
