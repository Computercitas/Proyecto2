// DetailPage.tsx
import React from "react";
import { useLocation, useParams, useNavigate } from "react-router-dom";

// Define the interface for query result
interface QueryResult {
  track_id: string;
  track_name: string;
  track_artist: string;
  lyrics: string;
  row_position: number;
  similitudCoseno: number;
}

const DetailPage: React.FC = () => {
  const { state } = useLocation();
  const { trackId } = useParams();
  const navigate = useNavigate();
  const result = state?.result as QueryResult; // Get the result from state

  if (!result) {
    return <p>Details not found for track ID: {trackId}</p>;
  }

  const handleGoBack = () => {
    navigate(-1); // Navigates back to the previous page
  };

  return (
    <div>
      <h2>{result.track_name}</h2>
      <p><strong>Track ID:</strong> {result.track_id}</p>
      <p><strong>Track Name:</strong> {result.track_name}</p>
      <p><strong>Artist:</strong> {result.track_artist}</p>

      {/* Scrollable lyrics box */}
      <div style={{ maxHeight: '200px', overflowY: 'auto', padding: '10px', border: '1px solid #ccc' }}>
        <p><strong>Lyrics:</strong> {result.lyrics}</p>
      </div>

      <p><strong>Row Position:</strong> {result.row_position}</p>
      <p><strong>Cosine Similarity:</strong> {result.similitudCoseno.toFixed(2)}</p>

      {/* Go Back Button */}
      <button onClick={handleGoBack}>Go Back</button>
    </div>
  );
};

export default DetailPage;
