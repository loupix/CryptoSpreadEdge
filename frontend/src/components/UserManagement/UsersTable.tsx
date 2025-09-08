/**
 * Composant pour la gestion des utilisateurs
 */

import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Typography,
  Pagination,
  Alert,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  PersonAdd as PersonAddIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { useUsers, useDeleteUser } from '../../hooks/useDatabaseApi';
import { User } from '../../services/databaseApi';
import Sparkline from '../Charts/Sparkline';

interface UsersTableProps {
  onViewUser?: (user: User) => void;
  onEditUser?: (user: User) => void;
  refreshTrigger?: number;
}

const UsersTable: React.FC<UsersTableProps> = ({
  onViewUser,
  onEditUser,
  refreshTrigger = 0,
}) => {
  const [filters, setFilters] = useState({
    role: '',
    status: '',
    limit: 50,
    offset: 0,
  });
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const { data: usersData, loading, error, refetch } = useUsers({
    ...filters,
    offset: filters.offset * filters.limit,
  });

  const deleteUserMutation = useDeleteUser();

  const users = usersData?.users || [];
  const totalCount = usersData?.total_count || 0;
  const totalPages = Math.ceil(totalCount / filters.limit);

  const handleFilterChange = (field: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      offset: 0, // Reset to first page when filtering
    }));
  };

  const generateActivitySeries = (seedBase: number) => {
    const length = 20;
    const result: { value: number }[] = [];
    let value = Math.max(1, seedBase || 1);
    for (let i = 0; i < length; i++) {
      const rand = Math.sin((seedBase + i) * 12.9898) * 43758.5453;
      const delta = ((rand - Math.floor(rand)) - 0.5) * (value * 0.1);
      value = Math.max(0, value + delta);
      result.push({ value: Number(value.toFixed(2)) });
    }
    return result;
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setFilters(prev => ({
      ...prev,
      offset: page - 1,
    }));
  };

  const handleViewUser = (user: User) => {
    setSelectedUser(user);
    setShowDetails(true);
    onViewUser?.(user);
  };

  const handleEditUser = (user: User) => {
    onEditUser?.(user);
  };

  const handleDeleteUser = async (userId: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) {
      try {
        await deleteUserMutation.mutate(userId);
        refetch();
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
      }
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'error';
      case 'trader':
        return 'primary';
      case 'analyst':
        return 'info';
      case 'viewer':
        return 'default';
      case 'auditor':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'default';
      case 'suspended':
        return 'error';
      case 'pending_verification':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Administrateur';
      case 'trader':
        return 'Trader';
      case 'analyst':
        return 'Analyste';
      case 'viewer':
        return 'Observateur';
      case 'auditor':
        return 'Auditeur';
      default:
        return role;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return 'Actif';
      case 'inactive':
        return 'Inactif';
      case 'suspended':
        return 'Suspendu';
      case 'pending_verification':
        return 'En attente';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Erreur lors du chargement des utilisateurs: {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Filtres */}
      <Box display="flex" gap={2} mb={2} alignItems="center">
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Rôle</InputLabel>
          <Select
            value={filters.role}
            onChange={(e) => handleFilterChange('role', e.target.value)}
            label="Rôle"
          >
            <MenuItem value="">Tous</MenuItem>
            <MenuItem value="admin">Administrateur</MenuItem>
            <MenuItem value="trader">Trader</MenuItem>
            <MenuItem value="analyst">Analyste</MenuItem>
            <MenuItem value="viewer">Observateur</MenuItem>
            <MenuItem value="auditor">Auditeur</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Statut</InputLabel>
          <Select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            label="Statut"
          >
            <MenuItem value="">Tous</MenuItem>
            <MenuItem value="active">Actif</MenuItem>
            <MenuItem value="inactive">Inactif</MenuItem>
            <MenuItem value="suspended">Suspendu</MenuItem>
            <MenuItem value="pending_verification">En attente</MenuItem>
          </Select>
        </FormControl>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
        >
          Actualiser
        </Button>
        <Button
          variant="contained"
          startIcon={<PersonAddIcon />}
          onClick={() => {/* TODO: Implement create user */}}
        >
          Nouvel utilisateur
        </Button>
      </Box>

      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nom d'utilisateur</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Nom complet</TableCell>
              <TableCell>Rôle</TableCell>
              <TableCell>Statut</TableCell>
              <TableCell>Dernière connexion</TableCell>
              <TableCell>Connexions</TableCell>
              <TableCell>Activité</TableCell>
              <TableCell>Sécurité</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    {user.username}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {user.email}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {user.first_name && user.last_name 
                      ? `${user.first_name} ${user.last_name}`
                      : '-'
                    }
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={getRoleLabel(user.role)}
                    color={getRoleColor(user.role)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={getStatusLabel(user.status)}
                    color={getStatusColor(user.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {user.last_login 
                      ? format(new Date(user.last_login), 'dd/MM/yyyy HH:mm', { locale: fr })
                      : 'Jamais'
                    }
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {user.login_count}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ width: 120 }}>
                    <Sparkline
                      data={generateActivitySeries(user.login_count || 1)}
                      height={32}
                      color="#7aa2f7"
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Tooltip title={user.email_verified ? 'Email vérifié' : 'Email non vérifié'}>
                      <Chip
                        label="Email"
                        color={user.email_verified ? 'success' : 'default'}
                        size="small"
                        variant="outlined"
                      />
                    </Tooltip>
                    <Tooltip title={user.two_factor_enabled ? '2FA activé' : '2FA désactivé'}>
                      <Chip
                        label="2FA"
                        color={user.two_factor_enabled ? 'success' : 'default'}
                        size="small"
                        variant="outlined"
                      />
                    </Tooltip>
                  </Box>
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Tooltip title="Voir les détails">
                      <IconButton
                        size="small"
                        onClick={() => handleViewUser(user)}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Modifier">
                      <IconButton
                        size="small"
                        onClick={() => handleEditUser(user)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Supprimer">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteUser(user.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {totalPages > 1 && (
        <Box display="flex" justifyContent="center" mt={2}>
          <Pagination
            count={totalPages}
            page={filters.offset + 1}
            onChange={handlePageChange}
            color="primary"
          />
        </Box>
      )}

      {/* Dialog de détails */}
      <Dialog
        open={showDetails}
        onClose={() => setShowDetails(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Détails de l'utilisateur</DialogTitle>
        <DialogContent>
          {selectedUser && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedUser.username}
              </Typography>
              
              <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mt={2}>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Email
                  </Typography>
                  <Typography variant="body2">
                    {selectedUser.email}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Nom complet
                  </Typography>
                  <Typography variant="body2">
                    {selectedUser.first_name && selectedUser.last_name 
                      ? `${selectedUser.first_name} ${selectedUser.last_name}`
                      : '-'
                    }
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Rôle
                  </Typography>
                  <Chip
                    label={getRoleLabel(selectedUser.role)}
                    color={getRoleColor(selectedUser.role)}
                    size="small"
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Statut
                  </Typography>
                  <Chip
                    label={getStatusLabel(selectedUser.status)}
                    color={getStatusColor(selectedUser.status)}
                    size="small"
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Téléphone
                  </Typography>
                  <Typography variant="body2">
                    {selectedUser.phone || '-'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Fuseau horaire
                  </Typography>
                  <Typography variant="body2">
                    {selectedUser.timezone}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Langue
                  </Typography>
                  <Typography variant="body2">
                    {selectedUser.language}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Dernière connexion
                  </Typography>
                  <Typography variant="body2">
                    {selectedUser.last_login 
                      ? format(new Date(selectedUser.last_login), 'dd/MM/yyyy HH:mm:ss', { locale: fr })
                      : 'Jamais'
                    }
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Nombre de connexions
                  </Typography>
                  <Typography variant="body2">
                    {selectedUser.login_count}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Email vérifié
                  </Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={selectedUser.email_verified}
                        disabled
                        size="small"
                      />
                    }
                    label=""
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    2FA activé
                  </Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={selectedUser.two_factor_enabled}
                        disabled
                        size="small"
                      />
                    }
                    label=""
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Créé le
                  </Typography>
                  <Typography variant="body2">
                    {format(new Date(selectedUser.created_at), 'dd/MM/yyyy HH:mm:ss', { locale: fr })}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Modifié le
                  </Typography>
                  <Typography variant="body2">
                    {format(new Date(selectedUser.updated_at), 'dd/MM/yyyy HH:mm:ss', { locale: fr })}
                  </Typography>
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDetails(false)}>
            Fermer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UsersTable;