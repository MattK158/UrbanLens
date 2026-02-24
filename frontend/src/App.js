import { useState } from 'react';
import Map from './components/Map';
import NeighborhoodPanel from './components/NeighborhoodPanel';
import { useNeighborhoods } from './hooks/useNeighborhoods';
import './App.css';

export default function App() {
  const [selectedNeighborhood, setSelectedNeighborhood] = useState(null);
  const { neighborhoods, loading } = useNeighborhoods();

  return (
    <div className="app">
      <header className="header">
        <div className="logo">UrbanLens</div>
        <div className="subtitle">Austin Neighborhood Intelligence</div>
        {loading && <div className="loading-badge">Loading neighborhoods...</div>}
      </header>

      <div className="map-container">
        <Map
          neighborhoods={neighborhoods}
          onNeighborhoodClick={setSelectedNeighborhood}
        />
        {selectedNeighborhood && (
          <NeighborhoodPanel
            slug={selectedNeighborhood}
            onClose={() => setSelectedNeighborhood(null)}
          />
        )}
      </div>
    </div>
  );
}