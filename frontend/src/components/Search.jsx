import { useState } from 'react';

export default function Search({ neighborhoods, onNeighborhoodClick }) {
  const [query, setQuery] = useState('');
  const [focused, setFocused] = useState(false);

  const names = neighborhoods?.features?.map(f => ({
    name: f.properties.name,
    slug: f.properties.slug,
    score: f.properties.overall_score,
  })) || [];

  const filtered = query.length > 1
    ? names.filter(n => n.name.toLowerCase().includes(query.toLowerCase())).slice(0, 6)
    : [];

  return (
    <div style={{
      position: 'absolute',
      top: 16,
      left: '50%',
      transform: 'translateX(-50%)',
      width: 280,
      zIndex: 10,
    }}>
      <input
        type="text"
        placeholder="Search neighborhoods..."
        value={query}
        onChange={e => setQuery(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setTimeout(() => setFocused(false), 200)}
        style={{
          width: '100%',
          padding: '10px 14px',
          background: 'rgba(0,0,0,0.85)',
          border: '1px solid #333',
          borderRadius: filtered.length > 0 && focused ? '8px 8px 0 0' : 8,
          color: '#fff',
          fontSize: 13,
          outline: 'none',
        }}
      />
      {focused && filtered.length > 0 && (
        <div style={{
          background: 'rgba(0,0,0,0.95)',
          border: '1px solid #333',
          borderTop: 'none',
          borderRadius: '0 0 8px 8px',
          overflow: 'hidden',
        }}>
          {filtered.map(n => (
            <div
              key={n.slug}
              onMouseDown={() => {
                onNeighborhoodClick(n.slug);
                setQuery('');
              }}
              style={{
                padding: '8px 14px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: 13,
                color: '#fff',
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#222'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <span>{n.name}</span>
              {n.score && (
                <span style={{
                  fontSize: 11,
                  color: n.score >= 50 ? '#2ecc71' : '#e74c3c',
                  fontWeight: 'bold',
                }}>
                  {Math.round(n.score)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}