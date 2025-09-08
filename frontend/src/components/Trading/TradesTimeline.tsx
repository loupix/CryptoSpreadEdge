import React from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';

interface TradeItem { id: string; time: string; symbol: string; side: 'buy'|'sell'; price: number; qty: number }

interface TradesTimelineProps { items: TradeItem[] }

const TradesTimeline: React.FC<TradesTimelineProps> = ({ items }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>Trades</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {items.map(t => (
            <Box key={t.id} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="caption" color="text.secondary">{t.time}</Typography>
                <Chip label={t.symbol} size="small" />
                <Chip label={t.side.toUpperCase()} size="small" color={t.side==='buy'?'success':'error'} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2">{t.qty}</Typography>
                <Typography variant="body2" color="text.secondary">@ {t.price.toFixed(2)}</Typography>
              </Box>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default TradesTimeline;

