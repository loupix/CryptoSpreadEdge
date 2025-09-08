import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface FlowPoint { timestamp: number | string; delta: number; cvd: number; }

interface OrderFlowChartProps {
  title?: string;
  data: FlowPoint[];
  height?: number;
}

const OrderFlowChart: React.FC<OrderFlowChartProps> = ({ title, data, height = 180 }) => {
  return (
    <Card variant="outlined">
      <CardContent>
        {title && <Typography variant="subtitle1" gutterBottom>{title}</Typography>}
        <div style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2430" />
              <XAxis dataKey="timestamp" tickFormatter={(v) => new Date(v).toLocaleTimeString()} stroke="#9aa4b2" />
              <YAxis stroke="#9aa4b2" />
              <Tooltip contentStyle={{ background: '#111418', border: '1px solid #1f2430' }} />
              <Area type="monotone" dataKey="delta" stroke="#ef4444" fill="#ef4444" fillOpacity={0.18} />
              <Area type="monotone" dataKey="cvd" stroke="#7aa2f7" fill="#7aa2f7" fillOpacity={0.14} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default OrderFlowChart;

