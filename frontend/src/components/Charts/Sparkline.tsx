import React from 'react';
import { ResponsiveContainer, LineChart, Line, Tooltip } from 'recharts';

interface SparklineProps {
  data: { value: number }[];
  height?: number;
  color?: string;
}

const Sparkline: React.FC<SparklineProps> = ({ data, height = 60, color = '#22c55e' }) => {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 0, left: 0, bottom: 0 }}>
          <Tooltip
            formatter={(val: any) => [Number(val).toLocaleString(), 'Valeur']}
            contentStyle={{ background: '#111418', border: '1px solid #1f2430' }}
          />
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Sparkline;

