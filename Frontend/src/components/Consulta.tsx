// src/components/Consulta.tsx

import React, { useState } from "react";

const Consulta: React.FC = () => {
  const [query, setQuery] = useState<string>("");

  const handleQueryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  };

  const handleSubmit = () => {
    // Aquí puedes hacer la lógica para realizar la consulta
    console.log("Consulta realizada:", query);
  };

  return (
    <div className="consulta-container">
      <h2>Realiza tu consulta</h2>
      <input
        type="text"
        value={query}
        onChange={handleQueryChange}
        placeholder="Ingresa tu consulta SQL"
      />
      <button onClick={handleSubmit}>Buscar</button>
    </div>
  );
};

export default Consulta;
