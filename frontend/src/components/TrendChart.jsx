import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { getTrends } from '../api/client';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const COLORS = {
  crime: '#e74c3c',
  traffic: '#f39c12',
  permits: '#2ecc71',
  code_complaints: '#3498db',
};

export default function TrendChart({ neighborhood }) {
  const [data, setData] = useState([]);
  const [dataset, setDataset] = useState('crime');

  useEffect(() => {
    if (!neighborhood) return;
    getTrends(dataset, neighborhood, 12).then(res => {
      const formatted = res.data.map(d => ({
        name: `${MONTHS[d.month - 1]} ${d.year}`,
        count: d.count,
      }));
      setData(formatted);
    });
  }, [neighborhood, dataset]);

  return (
    <div>
      <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
        {Object.keys(COLORS).map(d => (
          <button
            key={d}
            onClick={() => setDataset(d)}
            style={{
              background: dataset === d ? COLORS[d] : 'transparent',
              color: '#fff',
              border: `1px solid ${COLORS[d]}`,
              borderRadius: 4,
              padding: '4px 8px',
              cursor: 'pointer',
              fontSize: 10,
            }}
          >
            {d.replace('_', ' ')}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={data}>
          <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#999' }} />
          <YAxis tick={{ fontSize: 9, fill: '#999' }} />
          <Tooltip
            contentStyle={{ background: '#1a1a1a', border: 'none', fontSize: 11 }}
          />
          <Line
            type="monotone"
            dataKey="count"
            stroke={COLORS[dataset]}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}