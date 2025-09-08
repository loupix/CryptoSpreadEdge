import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material';

import { NewsItem } from '../../types/domain';

interface NewsFeedProps { items: NewsItem[] }

const NewsFeed: React.FC<NewsFeedProps> = ({ items }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>News</Typography>
        <List dense>
          {items.map((n: NewsItem) => (
            <ListItem key={n.id} divider>
              <ListItemText primary={n.title} secondary={`${n.source} • ${n.time}`} />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default NewsFeed;

