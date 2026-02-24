import { useEffect, useState } from 'react';
import { getNeighborhood } from '../api/client';
import ScoreCard from './ScoreCard';
import TrendChart from './TrendChart';

export default function NeighborhoodPanel({ slug, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    getNeighborhood(slug).then(res => {
      setData(res);
      setLoading(false);
    });
  }, [slug]);

  if (!slug) return null;

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      right: 0,
      width: 320,
      height: '100%',
      background: '#1a1a1a',
      color: '#fff',
      overflowY: 'auto',
      zIndex: 10,
      boxShadow: '-4px 0 20px rgba(0,0,0,0.5)',
    }}>
      <div style={{ padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 18 }}>{loading ? '...' : data?.name}</h2>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', color: '#fff',
            fontSize: 20, cursor: 'pointer'
          }}>×</button>
        </div>

        {loading ? (
          <p style={{ color: '#666' }}>Loading...</p>
        ) : data ? (
          <>
            {/* Rank */}
            <div style={{
              background: '#2a2a2a', borderRadius: 8, padding: 12, marginBottom: 16,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 32, fontWeight: 'bold', color: '#f39c12' }}>
                #{data.rank.overall}
              </div>
              <div style={{ fontSize: 12, color: '#999' }}>
                of {data.rank.of} neighborhoods
              </div>
            </div>

            {/* Scores */}
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ fontSize: 13, color: '#999', marginBottom: 12, textTransform: 'uppercase' }}>
                UrbanLens Score
              </h3>
              <ScoreCard scores={data.scores} />
            </div>

            {/* Stats */}
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ fontSize: 13, color: '#999', marginBottom: 12, textTransform: 'uppercase' }}>
                Last 90 Days
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  { label: 'Crime', value: data.stats.crime_incidents_90d, color: '#e74c3c' },
                  { label: 'Traffic', value: data.stats.traffic_incidents_90d, color: '#f39c12' },
                  { label: 'Permits', value: data.stats.permits_90d, color: '#2ecc71' },
                  { label: 'Complaints', value: data.stats.code_complaints_90d, color: '#3498db' },
                ].map(stat => (
                  <div key={stat.label} style={{
                    background: '#2a2a2a', borderRadius: 8, padding: 10, textAlign: 'center'
                  }}>
                    <div style={{ fontSize: 20, fontWeight: 'bold', color: stat.color }}>
                      {stat.value?.toLocaleString()}
                    </div>
                    <div style={{ fontSize: 11, color: '#999' }}>{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trend chart */}
            <div>
              <h3 style={{ fontSize: 13, color: '#999', marginBottom: 12, textTransform: 'uppercase' }}>
                12-Month Trend
              </h3>
              <TrendChart neighborhood={slug} />
            </div>
          </>
        ) : (
          <p style={{ color: '#666' }}>Failed to load neighborhood data.</p>
        )}
      </div>
    </div>
  );
}