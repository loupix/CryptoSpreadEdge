import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';

interface AlertsTickerProps {
  items: { id: string; text: string }[];
}

const AlertsTicker: React.FC<AlertsTickerProps> = ({ items }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>Alerte Ticker</Typography>
        <Box sx={{
          overflow: 'hidden',
          whiteSpace: 'nowrap',
          maskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)'
        }}>
          <Box sx={{
            display: 'inline-block',
            animation: 'ticker 20s linear infinite',
            '@keyframes ticker': {
              '0%': { transform: 'translateX(0)' },
              '100%': { transform: 'translateX(-50%)' },
            },
          }}>
            {[...items, ...items].map((it, idx) => (
              <Box key={it.id + '-' + idx} sx={{ display: 'inline-block', mr: 4, color: 'text.secondary' }}>
                {it.text}
              </Box>
            ))}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default AlertsTicker;

