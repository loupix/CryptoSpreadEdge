import React from 'react';
import { IconButton, Badge, Menu, MenuItem, ListItemText } from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';

interface NotificationsBellProps {
  items?: { id: string; title: string; time: string }[];
}

const NotificationsBell: React.FC<NotificationsBellProps> = ({ items = [] }) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const handleOpen = (e: React.MouseEvent<HTMLElement>) => setAnchorEl(e.currentTarget);
  const handleClose = () => setAnchorEl(null);

  return (
    <>
      <IconButton color="inherit" onClick={handleOpen} aria-label="notifications">
        <Badge badgeContent={items.length} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>
      <Menu anchorEl={anchorEl} open={open} onClose={handleClose} keepMounted>
        {items.length === 0 ? (
          <MenuItem disabled>Aucune notification</MenuItem>
        ) : (
          items.slice(0, 6).map((it: { id: string; title: string; time: string }) => (
            <MenuItem key={it.id} onClick={handleClose}>
              <ListItemText primary={it.title} secondary={it.time} />
            </MenuItem>
          ))
        )}
      </Menu>
    </>
  );
};

export default NotificationsBell;

