import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export interface VolumePoint {
  timestamp: number | string;
  volume: number;
}

interface VolumeBarChartProps {
  title?: string;
  data: VolumePoint[];
  height?: number;
  color?: string;
  timestampFormatter?: (ts: number | string) => string;
  valueFormatter?: (v: number) => string;
  outlined?: boolean;
}

const defaultTimestampFormatter = (ts: number | string) => {
  const date = typeof ts === 'number' ? new Date(ts) : new Date(ts);
  return date.toLocaleTimeString();
};

const defaultValueFormatter = (v: number) => v.toLocaleString();

const VolumeBarChart: React.FC<VolumeBarChartProps> = ({
  title,
  data,
  height = 140,
  color = '#7aa2f7',
  timestampFormatter = defaultTimestampFormatter,
  valueFormatter = defaultValueFormatter,
  outlined = false,
}) => {
  const content = (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2430" />
          <XAxis dataKey="timestamp" tickFormatter={timestampFormatter} stroke="#9aa4b2" />
          <YAxis tickFormatter={valueFormatter} stroke="#9aa4b2" />
          <Tooltip
            formatter={(val: any) => [valueFormatter(val as number), 'Volume']}
            labelFormatter={timestampFormatter}
            contentStyle={{ background: '#111418', border: '1px solid #1f2430' }}
          />
          <Bar dataKey="volume" fill={color} opacity={0.9} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );

  if (title || outlined) {
    return (
      <Card variant={outlined ? 'outlined' : undefined}>
        <CardContent>
          {title && (
            <Typography variant="subtitle1" gutterBottom>
              {title}
            </Typography>
          )}
          {content}
        </CardContent>
      </Card>
    );
  }

  return content;
};

export default React.memo(VolumeBarChart);

