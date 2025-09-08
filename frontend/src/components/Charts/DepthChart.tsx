import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface Level { price: number; size: number; }
interface DepthChartProps {
  bids: Level[];
  asks: Level[];
  height?: number;
  title?: string;
}

const DepthChart: React.FC<DepthChartProps> = ({ bids, asks, height = 200, title }) => {
  const sortedBids = [...bids].sort((a, b) => b.price - a.price);
  const sortedAsks = [...asks].sort((a, b) => a.price - b.price);
  let cum = 0;
  const bidData = sortedBids.map(l => ({ price: l.price, size: (cum += l.size) }));
  cum = 0;
  const askData = sortedAsks.map(l => ({ price: l.price, size: (cum += l.size) }));
  const data = [...bidData, ...askData];

  return (
    <Card>
      <CardContent>
        {title && <Typography variant="subtitle1" gutterBottom>{title}</Typography>}
        <div style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <XAxis dataKey="price" stroke="#9aa4b2" tickFormatter={(v) => v.toFixed(2)} />
              <YAxis dataKey="size" stroke="#9aa4b2" />
              <Tooltip contentStyle={{ background: '#111418', border: '1px solid #1f2430' }} />
              <Area dataKey="size" data={bidData} type="monotone" stroke="#22c55e" fill="#22c55e" fillOpacity={0.15} />
              <Area dataKey="size" data={askData} type="monotone" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default React.memo(DepthChart);

