import React from 'react';
import { Card, CardContent, Typography, Chip, Box, Button } from '@mui/material';

interface PositionItem {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  qty: number;
  entry: number;
  pnl: number;
}

interface OpenPositionsCompactProps {
  items: PositionItem[];
  onClose?: (id: string) => void;
}

const OpenPositionsCompact: React.FC<OpenPositionsCompactProps> = ({ items, onClose }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>Positions Ouvertes</Typography>
        {items.length === 0 ? (
          <Typography variant="body2" color="text.secondary">Aucune position</Typography>
        ) : (
          items.map((p) => (
            <Box key={p.id} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label={p.symbol} size="small" />
                <Chip label={p.side.toUpperCase()} size="small" color={p.side === 'long' ? 'success' : 'error'} />
                <Typography variant="body2">{p.qty}</Typography>
                <Typography variant="body2" color="text.secondary">@ {p.entry.toFixed(2)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label={`${p.pnl >= 0 ? '+' : ''}${p.pnl.toFixed(2)}$`} size="small" color={p.pnl >= 0 ? 'success' : 'error'} />
                <Button size="small" variant="outlined" color="error" onClick={() => onClose?.(p.id)}>Fermer</Button>
              </Box>
            </Box>
          ))
        )}
      </CardContent>
    </Card>
  );
};

export default OpenPositionsCompact;

