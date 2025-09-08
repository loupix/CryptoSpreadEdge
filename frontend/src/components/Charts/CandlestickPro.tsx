import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

interface Candle { timestamp: number; open: number; high: number; low: number; close: number; }

interface CandlestickProProps {
  title?: string;
  data: Candle[];
  height?: number;
  showMA?: boolean;
}

const computeMA = (data: Candle[], period: number) => {
  const out: { timestamp: number; value: number }[] = [];
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - period + 1);
    const slice = data.slice(start, i + 1);
    const avg = slice.reduce((s, d) => s + d.close, 0) / slice.length;
    out.push({ timestamp: data[i].timestamp, value: avg });
  }
  return out;
};

const CandlestickPro: React.FC<CandlestickProProps> = ({ title, data, height = 260, showMA = true }) => {
  const ma20 = computeMA(data, 20);
  const ma50 = computeMA(data, 50);
  const lineData = data.map(d => ({ timestamp: d.timestamp, close: d.close }));
  return (
    <Card>
      <CardContent>
        {title && <Typography variant="h6" gutterBottom>{title}</Typography>}
        <div style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={lineData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2430" />
              <XAxis dataKey="timestamp" tickFormatter={(v) => new Date(v).toLocaleTimeString()} stroke="#9aa4b2" />
              <YAxis stroke="#9aa4b2" />
              <Tooltip contentStyle={{ background: '#111418', border: '1px solid #1f2430' }} />
              <Line type="monotone" dataKey="close" stroke="#e6eaf2" dot={false} strokeWidth={1.6} />
              {showMA && <Line type="monotone" data={ma20} dataKey="value" stroke="#7aa2f7" dot={false} strokeWidth={1} />}
              {showMA && <Line type="monotone" data={ma50} dataKey="value" stroke="#22c55e" dot={false} strokeWidth={1} />}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default CandlestickPro;

