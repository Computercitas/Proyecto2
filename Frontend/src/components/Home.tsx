import { Link } from "react-router-dom";
import { FaGithub } from "react-icons/fa";
import "../App.css";

const Home = () => {
  return (
    <div className="home-container">
      <div className="content-overlay">
        <h1 className="welcome-title">Welcome!</h1>
        <p className="description">
        Discover and query the world of music on Spotify. Use our inverted index and select your preferred indexing method to perform free-text queries.
        </p>
        <div className="button-container">
          <Link to="/consulta">
            <button className="consulta-button">Start</button>
          </Link>
          <a
            href="https://github.com/Dateadores/Proyecto2"
            target="_blank"
            rel="noopener noreferrer"
          >
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
