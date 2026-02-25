import { useState, useEffect } from 'react';
import { compareNeighborhoods } from '../api/client';
import ScoreCard from './ScoreCard';

export default function ComparePanel({ slug1, slug2, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug1 || !slug2) return;
    setLoading(true);
    compareNeighborhoods(slug1, slug2).then(res => {
      setData(res);
      setLoading(false);
    });
  }, [slug1, slug2]);

  if (!slug1 || !slug2) return null;

  return (
    <div style={{
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      background: 'rgba(0,0,0,0.92)',
      color: '#fff',
      padding: '16px 24px',
      zIndex: 10,
      borderTop: '1px solid #333',
      maxHeight: '45vh',
      overflowY: 'auto',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={{ margin: 0, fontSize: 14, color: '#ccc', textTransform: 'uppercase' }}>
          Neighborhood Comparison
        </h3>
        <button onClick={onClose} style={{
          background: 'none', border: 'none', color: '#fff', fontSize: 20, cursor: 'pointer'
        }}>×</button>
      </div>

      {loading ? (
        <p style={{ color: '#666', fontSize: 13 }}>Loading comparison...</p>
      ) : data ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          {[data.neighborhood_1, data.neighborhood_2].map((n, i) => (
            <div key={i}>
              <div style={{ marginBottom: 12 }}>
                <h4 style={{ margin: '0 0 4px', fontSize: 16 }}>{n.name}</h4>
                <span style={{ fontSize: 12, color: '#666' }}>
                  Rank #{n.rank.overall} of {n.rank.of}
                </span>
              </div>

              <ScoreCard scores={n.scores} />

              <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                {[
                  { label: 'Crime', value: n.stats.crime_incidents_90d, color: '#e74c3c' },
                  { label: 'Traffic', value: n.stats.traffic_incidents_90d, color: '#f39c12' },
                  { label: 'Permits', value: n.stats.permits_90d, color: '#2ecc71' },
                  { label: 'Complaints', value: n.stats.code_complaints_90d, color: '#3498db' },
                ].map(stat => (
                  <div key={stat.label} style={{
                    background: '#1a1a1a', borderRadius: 6, padding: 8, textAlign: 'center'
                  }}>
                    <div style={{ fontSize: 16, fontWeight: 'bold', color: stat.color }}>
                      {stat.value?.toLocaleString()}
                    </div>
                    <div style={{ fontSize: 10, color: '#666' }}>{stat.label} (90d)</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p style={{ color: '#666' }}>Failed to load comparison.</p>
      )}
    </div>
  );
}