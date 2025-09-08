import React from 'react';
import { Box, Typography } from '@mui/material';

interface OrderLevel {
  price: number;
  size: number;
}

interface OrderBookMiniProps {
  bids: OrderLevel[];
  asks: OrderLevel[];
  maxLevels?: number;
  height?: number;
}

const OrderBookMini: React.FC<OrderBookMiniProps> = ({ bids, asks, maxLevels = 8, height = 160 }) => {
  const topBids = bids.slice(0, maxLevels);
  const topAsks = asks.slice(0, maxLevels);

  const maxBidSize = Math.max(...topBids.map(l => l.size), 1);
  const maxAskSize = Math.max(...topAsks.map(l => l.size), 1);

  const totalBid = topBids.reduce((s, l) => s + l.size, 0);
  const totalAsk = topAsks.reduce((s, l) => s + l.size, 0);
  const imbalance = totalBid + totalAsk > 0 ? (totalBid - totalAsk) / (totalBid + totalAsk) : 0;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="subtitle2">Order Book</Typography>
        <Typography variant="caption" color={imbalance >= 0 ? 'success.main' : 'error.main'}>
          Imbalance: {(imbalance * 100).toFixed(0)}%
        </Typography>
      </Box>
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, height }}>
        <Box>
          {topBids.map((l, idx) => (
            <Box key={idx} sx={{ position: 'relative', display: 'flex', justifyContent: 'space-between', fontSize: 12, lineHeight: '20px', mb: 0.5 }}>
              <Box sx={{ position: 'absolute', right: 0, left: `${100 - (l.size / maxBidSize) * 100}%`, top: 0, bottom: 0, backgroundColor: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)' }} />
              <Box sx={{ position: 'relative' }}>{l.price.toFixed(2)}</Box>
              <Box sx={{ position: 'relative' }}>{l.size.toFixed(4)}</Box>
            </Box>
          ))}
        </Box>
        <Box>
          {topAsks.map((l, idx) => (
            <Box key={idx} sx={{ position: 'relative', display: 'flex', justifyContent: 'space-between', fontSize: 12, lineHeight: '20px', mb: 0.5 }}>
              <Box sx={{ position: 'absolute', left: 0, right: `${100 - (l.size / maxAskSize) * 100}%`, top: 0, bottom: 0, backgroundColor: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }} />
              <Box sx={{ position: 'relative' }}>{l.price.toFixed(2)}</Box>
              <Box sx={{ position: 'relative' }}>{l.size.toFixed(4)}</Box>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
};

export default OrderBookMini;

