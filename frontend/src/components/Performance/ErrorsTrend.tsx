import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface ErrorsPoint { timestamp: number | string; errorsPerMin: number }

interface ErrorsTrendProps { data: ErrorsPoint[]; title?: string; height?: number }

const ErrorsTrend: React.FC<ErrorsTrendProps> = ({ data, title = 'Erreurs / min', height = 180 }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle1" gutterBottom>{title}</Typography>
        <div style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2430" />
              <XAxis dataKey="timestamp" tickFormatter={(v) => new Date(v).toLocaleTimeString()} stroke="#9aa4b2" />
              <YAxis stroke="#9aa4b2" />
              <Tooltip contentStyle={{ background: '#111418', border: '1px solid #1f2430' }} />
              <Area type="monotone" dataKey="errorsPerMin" stroke="#ef4444" fill="#ef4444" fillOpacity={0.18} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default ErrorsTrend;

