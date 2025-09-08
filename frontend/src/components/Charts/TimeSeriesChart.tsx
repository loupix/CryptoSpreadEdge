import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';
import {
  ResponsiveContainer,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Line,
  AreaChart,
  Area,
} from 'recharts';

export interface TimeSeriesPoint {
  timestamp: number | string;
  value: number;
}

interface TimeSeriesChartProps {
  title?: string;
  data: TimeSeriesPoint[];
  height?: number;
  variant?: 'line' | 'area';
  color?: string;
  valueFormatter?: (value: number) => string;
  timestampFormatter?: (ts: number | string) => string;
}

const defaultValueFormatter = (v: number) => v.toLocaleString();
const defaultTimestampFormatter = (ts: number | string) => {
  const date = typeof ts === 'number' ? new Date(ts) : new Date(ts);
  return date.toLocaleTimeString();
};

const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  title,
  data,
  height = 300,
  variant = 'line',
  color = '#00e19d',
  valueFormatter = defaultValueFormatter,
  timestampFormatter = defaultTimestampFormatter,
}) => {
  const chartColor = color;

  return (
    <Card>
      <CardContent>
        {title && (
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
        )}
        <div style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            {variant === 'area' ? (
              <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2430" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={timestampFormatter}
                  stroke="#9aa4b2"
                />
                <YAxis
                  tickFormatter={valueFormatter}
                  stroke="#9aa4b2"
                />
                <Tooltip
                  formatter={(val: any) => [valueFormatter(val as number), 'Valeur']}
                  labelFormatter={timestampFormatter}
                  contentStyle={{ background: '#111418', border: '1px solid #1f2430' }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={chartColor}
                  fill={chartColor}
                  fillOpacity={0.16}
                  strokeWidth={2}
                />
              </AreaChart>
            ) : (
              <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2430" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={timestampFormatter}
                  stroke="#9aa4b2"
                />
                <YAxis
                  tickFormatter={valueFormatter}
                  stroke="#9aa4b2"
                />
                <Tooltip
                  formatter={(val: any) => [valueFormatter(val as number), 'Valeur']}
                  labelFormatter={timestampFormatter}
                  contentStyle={{ background: '#111418', border: '1px solid #1f2430' }}
                />
                <Line type="monotone" dataKey="value" stroke={chartColor} strokeWidth={2} dot={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default TimeSeriesChart;

