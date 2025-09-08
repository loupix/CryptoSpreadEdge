/**
 * Page de gestion des utilisateurs
 */

import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  // Chip,
  Alert,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  People as PeopleIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  // Add as AddIcon,
  // Edit as EditIcon,
} from '@mui/icons-material';
import UsersTable from '../components/UserManagement/UsersTable';
import AlertsManager from '../components/Alerts/AlertsManager';
import { 
  useUsers, 
  useCreateUser, 
  useUpdateUser,
  useSecuritySummary,
  useNotifications 
} from '../hooks/useDatabaseApi';
import { User, Notification } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`user-tabpanel-${index}`}
      aria-labelledby={`user-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const UserManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [newUser, setNewUser] = useState<Partial<User>>({
    username: '',
    email: '',
    role: 'viewer',
    status: 'pending_verification',
    timezone: 'Europe/Paris',
    language: 'fr',
    email_verified: false,
    phone_verified: false,
    two_factor_enabled: false,
    login_count: 0,
  });

  // Hooks pour les données
  const { data: usersData, loading: usersLoading } = useUsers();
  const { data: securitySummary, loading: securityLoading } = useSecuritySummary();
  const { data: notificationsData, loading: notificationsLoading } = useNotifications({
    limit: 10,
  });

  const createUserMutation = useCreateUser();
  const updateUserMutation = useUpdateUser();

  const users: User[] = usersData?.users || [];
  const notifications: Notification[] = notificationsData?.notifications || [];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleCreateUser = async () => {
    try {
      await createUserMutation.mutate(newUser);
      setShowCreateDialog(false);
      setNewUser({
        username: '',
        email: '',
        role: 'viewer',
        status: 'pending_verification',
        timezone: 'Europe/Paris',
        language: 'fr',
        email_verified: false,
        phone_verified: false,
        two_factor_enabled: false,
        login_count: 0,
      });
    } catch (error) {
      console.error('Erreur lors de la création:', error);
    }
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setShowEditDialog(true);
  };

  const handleUpdateUser = async () => {
    if (selectedUser) {
      try {
        await updateUserMutation.mutate({
          id: selectedUser.id,
          data: selectedUser,
        });
        setShowEditDialog(false);
        setSelectedUser(null);
      } catch (error) {
        console.error('Erreur lors de la mise à jour:', error);
      }
    }
  };

  // const getRoleColor = (role: string) => {
  //   switch (role) {
  //     case 'admin':
  //       return 'error';
  //     case 'trader':
  //       return 'primary';
  //     case 'analyst':
  //       return 'info';
  //     case 'viewer':
  //       return 'default';
  //     case 'auditor':
  //       return 'warning';
  //     default:
  //       return 'default';
  //   }
  // };

  // const getStatusColor = (status: string) => {
  //   switch (status) {
  //     case 'active':
  //       return 'success';
  //     case 'inactive':
  //       return 'default';
  //     case 'suspended':
  //       return 'error';
  //     case 'pending_verification':
  //       return 'warning';
  //     default:
  //       return 'default';
  //   }
  // };

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Gestion des Utilisateurs
        </Typography>
        <Typography variant="body1" color="textSecondary" gutterBottom>
          Administration des utilisateurs, rôles et permissions
        </Typography>
      </Box>

      {/* Résumé des utilisateurs */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Total des utilisateurs */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<PeopleIcon color="primary" />}
              title="Total Utilisateurs"
              subheader="Tous les comptes"
            />
            <CardContent>
              {usersLoading ? (
                <CircularProgress size={24} />
              ) : (
                <Typography variant="h6" color="primary">
                  {users.length}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Utilisateurs actifs */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<PeopleIcon color="success" />}
              title="Utilisateurs Actifs"
              subheader="Comptes actifs"
            />
            <CardContent>
              {usersLoading ? (
                <CircularProgress size={24} />
              ) : (
                <Typography variant="h6" color="success.main">
                  {users.filter((u: User) => u.status === 'active').length}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Événements de sécurité */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<SecurityIcon color="warning" />}
              title="Événements Sécurité"
              subheader="Dernières 24h"
            />
            <CardContent>
              {securityLoading ? (
                <CircularProgress size={24} />
              ) : securitySummary ? (
                <Typography variant="h6" color="warning.main">
                  {securitySummary.recent_events || 0}
                </Typography>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  N/A
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Notifications en attente */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<NotificationsIcon color="info" />}
              title="Notifications"
              subheader="En attente"
            />
            <CardContent>
              {notificationsLoading ? (
                <CircularProgress size={24} />
              ) : (
                <Typography variant="h6" color="info.main">
                  {notifications.filter(n => !n.is_sent).length}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Onglets */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="user management tabs">
            <Tab label="Utilisateurs" icon={<PeopleIcon />} />
            <Tab label="Sécurité" icon={<SecurityIcon />} />
            <Tab label="Notifications" icon={<NotificationsIcon />} />
            <Tab label="Paramètres" icon={<SettingsIcon />} />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <UsersTable
            onEditUser={handleEditUser}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <AlertsManager />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Notifications
            </Typography>
            <Alert severity="info">
              Composant de notifications en cours de développement...
            </Alert>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Paramètres Système
            </Typography>
            <Alert severity="info">
              Composant de paramètres en cours de développement...
            </Alert>
          </Box>
        </TabPanel>
      </Paper>

      {/* Dialog de création d'utilisateur */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Nouvel Utilisateur</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              label="Nom d'utilisateur"
              value={newUser.username}
              onChange={(e) => setNewUser(prev => ({ ...prev, username: e.target.value }))}
              fullWidth
              margin="normal"
            />
            <TextField
              label="Email"
              type="email"
              value={newUser.email}
              onChange={(e) => setNewUser(prev => ({ ...prev, email: e.target.value }))}
              fullWidth
              margin="normal"
            />
            <TextField
              label="Prénom"
              value={newUser.first_name || ''}
              onChange={(e) => setNewUser(prev => ({ ...prev, first_name: e.target.value }))}
              fullWidth
              margin="normal"
            />
            <TextField
              label="Nom"
              value={newUser.last_name || ''}
              onChange={(e) => setNewUser(prev => ({ ...prev, last_name: e.target.value }))}
              fullWidth
              margin="normal"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Rôle</InputLabel>
              <Select
                value={newUser.role}
                onChange={(e) => setNewUser(prev => ({ ...prev, role: e.target.value as any }))}
                label="Rôle"
              >
                <MenuItem value="viewer">Observateur</MenuItem>
                <MenuItem value="trader">Trader</MenuItem>
                <MenuItem value="analyst">Analyste</MenuItem>
                <MenuItem value="auditor">Auditeur</MenuItem>
                <MenuItem value="admin">Administrateur</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Statut</InputLabel>
              <Select
                value={newUser.status}
                onChange={(e) => setNewUser(prev => ({ ...prev, status: e.target.value as any }))}
                label="Statut"
              >
                <MenuItem value="pending_verification">En attente</MenuItem>
                <MenuItem value="active">Actif</MenuItem>
                <MenuItem value="inactive">Inactif</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Téléphone"
              value={newUser.phone || ''}
              onChange={(e) => setNewUser(prev => ({ ...prev, phone: e.target.value }))}
              fullWidth
              margin="normal"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={newUser.two_factor_enabled}
                  onChange={(e) => setNewUser(prev => ({ ...prev, two_factor_enabled: e.target.checked }))}
                />
              }
              label="Activer l'authentification à deux facteurs"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>
            Annuler
          </Button>
          <Button 
            onClick={handleCreateUser}
            variant="contained"
            disabled={createUserMutation.loading}
          >
            {createUserMutation.loading ? 'Création...' : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de modification d'utilisateur */}
      <Dialog
        open={showEditDialog}
        onClose={() => setShowEditDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Modifier l'Utilisateur</DialogTitle>
        <DialogContent>
          {selectedUser && (
            <Box sx={{ pt: 2 }}>
              <TextField
                label="Nom d'utilisateur"
                value={selectedUser.username}
                onChange={(e) => setSelectedUser(prev => prev ? { ...prev, username: e.target.value } : null)}
                fullWidth
                margin="normal"
              />
              <TextField
                label="Email"
                type="email"
                value={selectedUser.email}
                onChange={(e) => setSelectedUser(prev => prev ? { ...prev, email: e.target.value } : null)}
                fullWidth
                margin="normal"
              />
              <FormControl fullWidth margin="normal">
                <InputLabel>Rôle</InputLabel>
                <Select
                  value={selectedUser.role}
                  onChange={(e) => setSelectedUser(prev => prev ? { ...prev, role: e.target.value as any } : null)}
                  label="Rôle"
                >
                  <MenuItem value="viewer">Observateur</MenuItem>
                  <MenuItem value="trader">Trader</MenuItem>
                  <MenuItem value="analyst">Analyste</MenuItem>
                  <MenuItem value="auditor">Auditeur</MenuItem>
                  <MenuItem value="admin">Administrateur</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth margin="normal">
                <InputLabel>Statut</InputLabel>
                <Select
                  value={selectedUser.status}
                  onChange={(e) => setSelectedUser(prev => prev ? { ...prev, status: e.target.value as any } : null)}
                  label="Statut"
                >
                  <MenuItem value="active">Actif</MenuItem>
                  <MenuItem value="inactive">Inactif</MenuItem>
                  <MenuItem value="suspended">Suspendu</MenuItem>
                  <MenuItem value="pending_verification">En attente</MenuItem>
                </Select>
              </FormControl>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>
            Annuler
          </Button>
          <Button 
            onClick={handleUpdateUser}
            variant="contained"
            disabled={updateUserMutation.loading}
          >
            {updateUserMutation.loading ? 'Mise à jour...' : 'Mettre à jour'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement;