import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Home from "./components/Home";
import Consulta from "./components/Consulta";
import DetailPage from "./components/DetailPage";

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/consulta" element={<Consulta />} />
          <Route path="/details/:trackId" element={<DetailPage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;