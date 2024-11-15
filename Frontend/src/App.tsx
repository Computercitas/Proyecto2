import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Home from "./components/Home";
import Consulta from "./components/Consulta";
import Detalle from './components/Detalle'; // Este es el componente que mostraría los detalles de la canción

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/consulta" element={<Consulta />} />
          <Route path="/detalle" element={<Detalle />} />

        </Routes>
      </div>
    </Router>
  );
};

export default App;