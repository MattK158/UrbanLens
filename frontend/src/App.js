import { useState } from 'react';
import Map from './components/Map';
import NeighborhoodPanel from './components/NeighborhoodPanel';
import { useNeighborhoods } from './hooks/useNeighborhoods';
import './App.css';
import Leaderboard from './components/Leaderboard';
import Search from './components/Search';
import ComparePanel from './components/ComparePanel';

export default function App() {
  const [selectedNeighborhood, setSelectedNeighborhood] = useState(null);
  const { neighborhoods, loading } = useNeighborhoods();
  const [compareSlug, setCompareSlug] = useState(null);

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
        <Search neighborhoods={neighborhoods} onNeighborhoodClick={setSelectedNeighborhood} />
        <Leaderboard
          onNeighborhoodClick={setSelectedNeighborhood}
          hidden={!!selectedNeighborhood}
        />
        {compareSlug && selectedNeighborhood && compareSlug !== selectedNeighborhood && (
          <ComparePanel
            slug1={selectedNeighborhood}
            slug2={compareSlug}
            onClose={() => setCompareSlug(null)}
          />
        )}
        {compareSlug && !selectedNeighborhood && (
          <div style={{
            position: 'absolute',
            bottom: 40,
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#f39c12',
            color: '#000',
            padding: '10px 20px',
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 'bold',
            zIndex: 10,
          }}>
            Click a neighborhood to compare
          </div>
        )}
        {selectedNeighborhood && (
          <NeighborhoodPanel
            slug={selectedNeighborhood}
            onClose={() => setSelectedNeighborhood(null)}
            onCompare={(slug) => {
              setCompareSlug(slug);
              setSelectedNeighborhood(null);
            }}
          />
        )}
      </div>
    </div>
  );
}