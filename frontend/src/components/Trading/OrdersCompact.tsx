import React from 'react';
import { Card, CardContent, Typography, Chip, Box, IconButton, Tooltip } from '@mui/material';
import CancelIcon from '@mui/icons-material/Cancel';

interface OrderItem { id: string; symbol: string; side: 'buy'|'sell'; type: string; qty: number; price?: number; status: string }

interface OrdersCompactProps {
  items: OrderItem[];
  onCancel?: (id: string) => void;
}

const OrdersCompact: React.FC<OrdersCompactProps> = ({ items, onCancel }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>Ordres</Typography>
        {items.length === 0 ? (
          <Typography variant="body2" color="text.secondary">Aucun ordre</Typography>
        ) : (
          items.map(o => (
            <Box key={o.id} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label={o.symbol} size="small" />
                <Chip label={o.side.toUpperCase()} size="small" color={o.side==='buy'?'success':'error'} />
                <Chip label={o.type.toUpperCase()} size="small" />
                <Typography variant="body2">{o.qty}</Typography>
                {o.price && <Typography variant="body2" color="text.secondary">@ {o.price.toFixed(2)}</Typography>}
                <Chip label={o.status.toUpperCase()} size="small" color={o.status==='open'?'info':o.status==='pending'?'warning':'default'} />
              </Box>
              <Tooltip title="Annuler">
                <IconButton size="small" onClick={() => onCancel?.(o.id)}>
                  <CancelIcon />
                </IconButton>
              </Tooltip>
            </Box>
          ))
        )}
      </CardContent>
    </Card>
  );
};

export default OrdersCompact;

