export default function ScoreCard({ scores }) {
  if (!scores) return null;

  const scoreItems = [
    { label: 'Overall', value: scores.overall, color: getColor(scores.overall) },
    { label: 'Safety', value: scores.safety, color: getColor(scores.safety) },
    { label: 'Infrastructure', value: scores.infrastructure, color: getColor(scores.infrastructure) },
    { label: 'Traffic', value: scores.emergency_response, color: getColor(scores.emergency_response) },
    { label: 'Development', value: scores.development, color: getColor(scores.development) },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {scoreItems.map(item => (
        <div key={item.label}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 12, color: '#ccc' }}>{item.label}</span>
            <span style={{ fontSize: 12, fontWeight: 'bold', color: item.color }}>
              {item.value !== null ? Math.round(item.value) : 'N/A'}
            </span>
          </div>
          <div style={{ background: '#333', borderRadius: 4, height: 6 }}>
            <div style={{
              width: `${item.value || 0}%`,
              height: '100%',
              background: item.color,
              borderRadius: 4,
              transition: 'width 0.5s ease',
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function getColor(score) {
  if (score === null) return '#666';
  if (score >= 70) return '#2ecc71';
  if (score >= 40) return '#f39c12';
  return '#e74c3c';
}