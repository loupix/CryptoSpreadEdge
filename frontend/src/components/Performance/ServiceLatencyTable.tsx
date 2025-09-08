import React from 'react';
import { Card, CardContent, Typography, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material';

interface LatencyItem { name: string; status: string; response_time: number }

interface ServiceLatencyTableProps { items: LatencyItem[] }

const ServiceLatencyTable: React.FC<ServiceLatencyTableProps> = ({ items }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle1" gutterBottom>Latence par Service</Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Service</TableCell>
              <TableCell>Statut</TableCell>
              <TableCell align="right">Latence (ms)</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((it) => (
              <TableRow key={it.name}>
                <TableCell>{it.name}</TableCell>
                <TableCell>{it.status}</TableCell>
                <TableCell align="right">{it.response_time}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default ServiceLatencyTable;

