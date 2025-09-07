/**
 * Interface de configuration des exchanges
 */

import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Divider,
  Paper,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  VisibilityOff as HideIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  AccountBalance as AccountBalanceIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { useExchanges, useCreateUser } from '../../hooks/useDatabaseApi';
import { Exchange } from '../../services/databaseApi';

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
      id={`exchange-tabpanel-${index}`}
      aria-labelledby={`exchange-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ExchangeConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedExchange, setSelectedExchange] = useState<Exchange | null>(null);
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  
  // État pour le nouvel exchange
  const [newExchange, setNewExchange] = useState({
    name: '',
    display_name: '',
    exchange_type: 'centralized' as 'centralized' | 'decentralized' | 'hybrid',
    api_base_url: '',
    websocket_url: '',
    api_key: '',
    api_secret: '',
    passphrase: '',
    sandbox: false,
  });

  // Hooks pour les données
  const { data: exchangesData, loading, error, refetch } = useExchanges();

  const exchanges = exchangesData?.exchanges || [];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleAddExchange = async () => {
    try {
      // Ici, on créerait un nouvel exchange via l'API
      console.log('Ajout d\'un nouvel exchange:', newExchange);
      setShowAddDialog(false);
      setNewExchange({
        name: '',
        display_name: '',
        exchange_type: 'centralized',
        api_base_url: '',
        websocket_url: '',
        api_key: '',
        api_secret: '',
        passphrase: '',
        sandbox: false,
      });
      refetch();
    } catch (error) {
      console.error('Erreur lors de l\'ajout:', error);
    }
  };

  const handleEditExchange = (exchange: Exchange) => {
    setSelectedExchange(exchange);
    setShowEditDialog(true);
  };

  const handleDeleteExchange = async (exchangeId: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cette configuration d\'exchange ?')) {
      try {
        // Ici, on supprimerait l'exchange via l'API
        console.log('Suppression de l\'exchange:', exchangeId);
        refetch();
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
      }
    }
  };

  const handleTestConnection = async (exchangeId: string) => {
    try {
      // Ici, on testerait la connexion à l'exchange
      console.log('Test de connexion pour:', exchangeId);
    } catch (error) {
      console.error('Erreur lors du test:', error);
    }
  };

  const toggleApiKeyVisibility = (exchangeId: string) => {
    setShowApiKeys(prev => ({
      ...prev,
      [exchangeId]: !prev[exchangeId]
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'default';
      case 'maintenance':
        return 'warning';
      case 'suspended':
        return 'error';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon />;
      case 'inactive':
        return <WarningIcon />;
      case 'maintenance':
        return <WarningIcon />;
      case 'suspended':
        return <ErrorIcon />;
      case 'error':
        return <ErrorIcon />;
      default:
        return <WarningIcon />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'centralized':
        return 'primary';
      case 'decentralized':
        return 'secondary';
      case 'hybrid':
        return 'info';
      default:
        return 'default';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'centralized':
        return 'Centralisé';
      case 'decentralized':
        return 'Décentralisé';
      case 'hybrid':
        return 'Hybride';
      default:
        return type;
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
        Erreur lors du chargement des exchanges: {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Configuration des Exchanges
        </Typography>
        <Typography variant="body1" color="textSecondary" gutterBottom>
          Gestion des connexions et paramètres des plateformes de trading
        </Typography>
      </Box>

      {/* Statistiques */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<AccountBalanceIcon color="primary" />}
              title="Exchanges Configurés"
              subheader="Total"
            />
            <CardContent>
              <Typography variant="h6" color="primary">
                {exchanges.length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Plateformes disponibles
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<CheckCircleIcon color="success" />}
              title="Connexions Actives"
              subheader="Fonctionnelles"
            />
            <CardContent>
              <Typography variant="h6" color="success.main">
                {exchanges.filter(e => e.status === 'active').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Prêtes pour le trading
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<WarningIcon color="warning" />}
              title="En Maintenance"
              subheader="Temporairement indisponibles"
            />
            <CardContent>
              <Typography variant="h6" color="warning.main">
                {exchanges.filter(e => e.status === 'maintenance').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Retour prévu bientôt
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<ErrorIcon color="error" />}
              title="Erreurs"
              subheader="Nécessitent attention"
            />
            <CardContent>
              <Typography variant="h6" color="error.main">
                {exchanges.filter(e => e.status === 'error').length}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Vérification requise
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Onglets */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="exchange config tabs">
            <Tab label="Exchanges" icon={<AccountBalanceIcon />} />
            <Tab label="API Keys" icon={<SecurityIcon />} />
            <Tab label="Paramètres" icon={<SettingsIcon />} />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Liste des Exchanges</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setShowAddDialog(true)}
              >
                Ajouter un Exchange
              </Button>
            </Box>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Nom</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Statut</TableCell>
                    <TableCell>Pays</TableCell>
                    <TableCell>Fees Maker</TableCell>
                    <TableCell>Fees Taker</TableCell>
                    <TableCell>KYC Requis</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {exchanges.map((exchange) => (
                    <TableRow key={exchange.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {exchange.display_name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {exchange.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getTypeLabel(exchange.exchange_type)}
                          color={getTypeColor(exchange.exchange_type)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getStatusIcon(exchange.status)}
                          <Chip
                            label={exchange.status.toUpperCase()}
                            color={getStatusColor(exchange.status)}
                            size="small"
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {exchange.countries.join(', ')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {(exchange.trading_fees.maker * 100).toFixed(3)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {(exchange.trading_fees.taker * 100).toFixed(3)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={exchange.kyc_required ? 'OUI' : 'NON'}
                          color={exchange.kyc_required ? 'warning' : 'success'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" gap={1}>
                          <Tooltip title="Tester la connexion">
                            <IconButton
                              size="small"
                              onClick={() => handleTestConnection(exchange.id)}
                            >
                              <RefreshIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Modifier">
                            <IconButton
                              size="small"
                              onClick={() => handleEditExchange(exchange)}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Supprimer">
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteExchange(exchange.id)}
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
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Box>
            <Typography variant="h6" gutterBottom>Gestion des Clés API</Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Les clés API sont chiffrées et stockées de manière sécurisée. 
              Seuls les utilisateurs autorisés peuvent les voir.
            </Alert>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Exchange</TableCell>
                    <TableCell>Clé API</TableCell>
                    <TableCell>Dernière Utilisation</TableCell>
                    <TableCell>Statut</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {exchanges.map((exchange) => (
                    <TableRow key={exchange.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {exchange.display_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" fontFamily="monospace">
                            {showApiKeys[exchange.id] 
                              ? '••••••••••••••••' 
                              : '••••••••••••••••'
                            }
                          </Typography>
                          <IconButton
                            size="small"
                            onClick={() => toggleApiKeyVisibility(exchange.id)}
                          >
                            {showApiKeys[exchange.id] ? <HideIcon /> : <ViewIcon />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {format(new Date(exchange.updated_at), 'dd/MM/yyyy HH:mm', { locale: fr })}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label="CONFIGURÉE"
                          color="success"
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" gap={1}>
                          <Tooltip title="Tester">
                            <IconButton size="small">
                              <RefreshIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Modifier">
                            <IconButton size="small">
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Supprimer">
                            <IconButton size="small" color="error">
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
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Box>
            <Typography variant="h6" gutterBottom>Paramètres Globaux</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Sécurité" />
                  <CardContent>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Chiffrement des clés API"
                    />
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Rotation automatique des clés"
                    />
                    <FormControlLabel
                      control={<Switch />}
                      label="Validation 2FA pour les modifications"
                    />
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Monitoring" />
                  <CardContent>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Surveillance des connexions"
                    />
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Alertes de déconnexion"
                    />
                    <FormControlLabel
                      control={<Switch />}
                      label="Logs détaillés"
                    />
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>
      </Paper>

      {/* Dialog d'ajout d'exchange */}
      <Dialog
        open={showAddDialog}
        onClose={() => setShowAddDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Ajouter un Exchange</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Nom de l'exchange"
                  value={newExchange.name}
                  onChange={(e) => setNewExchange(prev => ({ ...prev, name: e.target.value }))}
                  fullWidth
                  margin="normal"
                />
                <TextField
                  label="Nom d'affichage"
                  value={newExchange.display_name}
                  onChange={(e) => setNewExchange(prev => ({ ...prev, display_name: e.target.value }))}
                  fullWidth
                  margin="normal"
                />
                <FormControl fullWidth margin="normal">
                  <InputLabel>Type</InputLabel>
                  <Select
                    value={newExchange.exchange_type}
                    onChange={(e) => setNewExchange(prev => ({ ...prev, exchange_type: e.target.value as any }))}
                    label="Type"
                  >
                    <MenuItem value="centralized">Centralisé</MenuItem>
                    <MenuItem value="decentralized">Décentralisé</MenuItem>
                    <MenuItem value="hybrid">Hybride</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  label="URL de l'API"
                  value={newExchange.api_base_url}
                  onChange={(e) => setNewExchange(prev => ({ ...prev, api_base_url: e.target.value }))}
                  fullWidth
                  margin="normal"
                />
                <TextField
                  label="URL WebSocket"
                  value={newExchange.websocket_url}
                  onChange={(e) => setNewExchange(prev => ({ ...prev, websocket_url: e.target.value }))}
                  fullWidth
                  margin="normal"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={newExchange.sandbox}
                      onChange={(e) => setNewExchange(prev => ({ ...prev, sandbox: e.target.checked }))}
                    />
                  }
                  label="Mode Sandbox"
                />
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Clés API (optionnel - peut être configuré plus tard)
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  label="Clé API"
                  type="password"
                  value={newExchange.api_key}
                  onChange={(e) => setNewExchange(prev => ({ ...prev, api_key: e.target.value }))}
                  fullWidth
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Secret API"
                  type="password"
                  value={newExchange.api_secret}
                  onChange={(e) => setNewExchange(prev => ({ ...prev, api_secret: e.target.value }))}
                  fullWidth
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Passphrase (si requis)"
                  type="password"
                  value={newExchange.passphrase}
                  onChange={(e) => setNewExchange(prev => ({ ...prev, passphrase: e.target.value }))}
                  fullWidth
                  margin="normal"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAddDialog(false)}>
            Annuler
          </Button>
          <Button onClick={handleAddExchange} variant="contained">
            Ajouter
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de modification d'exchange */}
      <Dialog
        open={showEditDialog}
        onClose={() => setShowEditDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Modifier l'Exchange</DialogTitle>
        <DialogContent>
          {selectedExchange && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="h6" gutterBottom>
                {selectedExchange.display_name}
              </Typography>
              <Alert severity="info">
                Modification des paramètres de l'exchange en cours de développement...
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>
            Fermer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExchangeConfig;