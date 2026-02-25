import { useState, useEffect } from 'react';
import { getScores } from '../api/client';

export default function Leaderboard({ onNeighborhoodClick }) {
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('top'); // 'top' or 'bottom'

  useEffect(() => {
    getScores().then(res => {
      setScores(res.scores);
      setLoading(false);
    });
  }, []);

  const displayed = view === 'top' ? scores.slice(0, 10) : scores.slice(-10).reverse();

  return (
    <div style={{
      position: 'absolute',
      top: 70,
      right: 16,
      width: 240,
      background: 'rgba(0,0,0,0.85)',
      borderRadius: 8,
      padding: 12,
      zIndex: 1,
      color: '#fff',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <button
          onClick={() => setView('top')}
          style={{
            flex: 1, padding: '4px 0', fontSize: 11, cursor: 'pointer',
            background: view === 'top' ? '#2ecc71' : 'transparent',
            color: '#fff', border: '1px solid #2ecc71', borderRadius: '4px 0 0 4px'
          }}
        >
          Top 10
        </button>
        <button
          onClick={() => setView('bottom')}
          style={{
            flex: 1, padding: '4px 0', fontSize: 11, cursor: 'pointer',
            background: view === 'bottom' ? '#e74c3c' : 'transparent',
            color: '#fff', border: '1px solid #e74c3c', borderRadius: '0 4px 4px 0'
          }}
        >
          Bottom 10
        </button>
      </div>

      {loading ? (
        <p style={{ fontSize: 11, color: '#666' }}>Loading...</p>
      ) : (
        displayed.map((n, i) => (
          <div
            key={n.slug}
            onClick={() => onNeighborhoodClick(n.slug)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '5px 4px', cursor: 'pointer', borderRadius: 4,
              transition: 'background 0.2s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#222'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <span style={{ fontSize: 10, color: '#666', width: 16 }}>
              {view === 'top' ? i + 1 : scores.length - 9 + i}
            </span>
            <span style={{ fontSize: 11, flex: 1 }}>{n.neighborhood}</span>
            <span style={{
              fontSize: 11, fontWeight: 'bold',
              color: n.overall >= 50 ? '#2ecc71' : '#e74c3c'
            }}>
              {Math.round(n.overall)}
            </span>
          </div>
        ))
      )}
    </div>
  );
}