import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';

interface HeatmapChartProps {
  title?: string;
  labelsX: string[];
  labelsY: string[];
  values: number[][]; // -1..1 for correlations
  height?: number;
}

const getColor = (v: number) => {
  const value = Math.max(-1, Math.min(1, v || 0));
  const red = value < 0 ? 239 : 0;
  const green = value > 0 ? 34 : 0;
  const blue = 68;
  const alpha = Math.min(0.85, Math.abs(value));
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
};

const HeatmapChart: React.FC<HeatmapChartProps> = ({ title, labelsX, labelsY, values, height = 240 }) => {
  const rows = labelsY.length;
  const cols = labelsX.length;
  return (
    <Card>
      <CardContent>
        {title && (
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
        )}
        <Box sx={{ display: 'grid', gridTemplateColumns: `80px repeat(${cols}, 1fr)`, gap: 0.5, alignItems: 'center' }}>
          <Box />
          {labelsX.map((lx) => (
            <Box key={lx} sx={{ textAlign: 'center', fontSize: 12, color: 'text.secondary' }}>{lx}</Box>
          ))}
          {labelsY.map((ly, r) => (
            <React.Fragment key={ly}>
              <Box sx={{ fontSize: 12, color: 'text.secondary' }}>{ly}</Box>
              {labelsX.map((lx, c) => (
                <Box
                  key={`${r}-${c}`}
                  sx={{
                    height: Math.max(18, height / Math.max(1, rows)),
                    backgroundColor: getColor(values[r]?.[c] ?? 0),
                    border: '1px solid rgba(255,255,255,0.06)',
                  }}
                />
              ))}
            </React.Fragment>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default HeatmapChart;

