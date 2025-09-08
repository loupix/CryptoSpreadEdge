import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  // IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  // Chip,
} from '@mui/material';
import MenuItem from '@mui/material/MenuItem';
import {
  Save,
  Refresh,
  Delete,
  // Add,
  // Edit,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';
import { apiClient } from '../services/api';

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Settings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [settings, setSettings] = useState({
    // API Settings
    apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    wsUrl: process.env.REACT_APP_WS_URL || 'ws://localhost:8000',
    timeout: 30000,
    
    // Trading Settings
    autoTrading: false,
    maxPositions: 5,
    riskLevel: 'medium',
    stopLoss: 5,
    takeProfit: 10,
    
    // Notification Settings
    emailNotifications: true,
    pushNotifications: false,
    soundAlerts: true,
    arbitrageAlerts: true,
    predictionAlerts: false,
    
    // Display Settings
    theme: 'dark',
    primaryColor: '#00e19d',
    secondaryColor: '#7aa2f7',
    language: 'fr',
    currency: 'USD',
    timezone: 'Europe/Paris',
    refreshInterval: 5000,
  });

  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<string | null>(null);

  useEffect(() => {
    loadHealthStatus();
  }, []);

  const loadHealthStatus = async () => {
    try {
      const healthData = await apiClient.getHealth();
      setHealth(healthData);
    } catch (err) {
      console.error('Health check error:', err);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const saveSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Simuler la sauvegarde des paramètres
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Sauvegarder dans localStorage
      localStorage.setItem('cryptospreadedge-settings', JSON.stringify(settings));
      if (settings.theme) {
        localStorage.setItem('cryptospreadedge-theme', settings.theme);
        const event = new CustomEvent('cryptospreadedge-theme-change', { detail: { mode: settings.theme, primary: settings.primaryColor, secondary: settings.secondaryColor } });
        window.dispatchEvent(event);
      }
      
      setSuccess('Paramètres sauvegardés avec succès');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Erreur lors de la sauvegarde des paramètres');
    } finally {
      setLoading(false);
    }
  };

  const resetSettings = () => {
    setSettings({
      apiUrl: 'http://localhost:8000',
      wsUrl: 'ws://localhost:8000',
      timeout: 30000,
      autoTrading: false,
      maxPositions: 5,
      riskLevel: 'medium',
      stopLoss: 5,
      takeProfit: 10,
      emailNotifications: true,
      pushNotifications: false,
      soundAlerts: true,
      arbitrageAlerts: true,
      predictionAlerts: false,
      theme: 'dark',
      primaryColor: '#00e19d',
      secondaryColor: '#7aa2f7',
      language: 'fr',
      currency: 'USD',
      timezone: 'Europe/Paris',
      refreshInterval: 5000,
    });
  };

  const testConnection = async () => {
    try {
      setLoading(true);
      await apiClient.getHealth();
      setSuccess('Connexion réussie');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteItem = (item: string) => {
    setItemToDelete(item);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    // Logique de suppression
    console.log('Suppression de:', itemToDelete);
    setDeleteDialogOpen(false);
    setItemToDelete(null);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle color="success" />;
      case 'degraded': return <Warning color="warning" />;
      case 'unhealthy': return <Error color="error" />;
      default: return <Error color="error" />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Paramètres
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="API & Connexion" />
              <Tab label="Trading" />
              <Tab label="Notifications" />
              <Tab label="Affichage" />
              <Tab label="Système" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Typography variant="h6" gutterBottom>
              Configuration API
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="URL de l'API"
                  value={settings.apiUrl}
                  onChange={(e) => handleSettingChange('apiUrl', e.target.value)}
                  helperText="URL de base pour les requêtes API"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="URL WebSocket"
                  value={settings.wsUrl}
                  onChange={(e) => handleSettingChange('wsUrl', e.target.value)}
                  helperText="URL pour les connexions WebSocket"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Timeout (ms)"
                  type="number"
                  value={settings.timeout}
                  onChange={(e) => handleSettingChange('timeout', parseInt(e.target.value))}
                  helperText="Délai d'attente pour les requêtes"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', height: '100%' }}>
                  <Button
                    variant="outlined"
                    onClick={testConnection}
                    disabled={loading}
                    startIcon={<Refresh />}
                  >
                    Tester la Connexion
                  </Button>
                </Box>
              </Grid>
            </Grid>

            {health && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Statut des Services
                </Typography>
                <List>
                  {Object.entries(health.services).map(([service, status]: [string, any]) => (
                    <ListItem key={service}>
                      <ListItemText
                        primary={service}
                        secondary={`${status.status} - ${status.response_time}ms`}
                      />
                      <ListItemSecondaryAction>
                        {getStatusIcon(status.status)}
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Typography variant="h6" gutterBottom>
              Configuration Trading
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoTrading}
                      onChange={(e) => handleSettingChange('autoTrading', e.target.checked)}
                    />
                  }
                  label="Trading Automatique"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Nombre Maximum de Positions"
                  type="number"
                  value={settings.maxPositions}
                  onChange={(e) => handleSettingChange('maxPositions', parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 20 }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Niveau de Risque"
                  value={settings.riskLevel}
                  onChange={(e) => handleSettingChange('riskLevel', e.target.value)}
                >
                  <MenuItem value="low">Faible</MenuItem>
                  <MenuItem value="medium">Moyen</MenuItem>
                  <MenuItem value="high">Élevé</MenuItem>
                </TextField>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Stop Loss (%)"
                  type="number"
                  value={settings.stopLoss}
                  onChange={(e) => handleSettingChange('stopLoss', parseFloat(e.target.value))}
                  inputProps={{ min: 0, max: 50, step: 0.1 }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Take Profit (%)"
                  type="number"
                  value={settings.takeProfit}
                  onChange={(e) => handleSettingChange('takeProfit', parseFloat(e.target.value))}
                  inputProps={{ min: 0, max: 100, step: 0.1 }}
                />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" gutterBottom>
              Notifications
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.emailNotifications}
                      onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                    />
                  }
                  label="Notifications par Email"
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.pushNotifications}
                      onChange={(e) => handleSettingChange('pushNotifications', e.target.checked)}
                    />
                  }
                  label="Notifications Push"
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.soundAlerts}
                      onChange={(e) => handleSettingChange('soundAlerts', e.target.checked)}
                    />
                  }
                  label="Alertes Sonores"
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.arbitrageAlerts}
                      onChange={(e) => handleSettingChange('arbitrageAlerts', e.target.checked)}
                    />
                  }
                  label="Alertes d'Arbitrage"
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.predictionAlerts}
                      onChange={(e) => handleSettingChange('predictionAlerts', e.target.checked)}
                    />
                  }
                  label="Alertes de Prédiction"
                />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Typography variant="h6" gutterBottom>
              Affichage
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Thème"
                  value={settings.theme}
                  onChange={(e) => handleSettingChange('theme', e.target.value)}
                >
                  <MenuItem value="dark">Sombre</MenuItem>
                  <MenuItem value="light">Clair</MenuItem>
                </TextField>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Couleur primaire"
                  type="color"
                  value={settings.primaryColor}
                  onChange={(e) => handleSettingChange('primaryColor', e.target.value)}
                  inputProps={{ style: { height: 48, padding: 0 } }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Couleur secondaire"
                  type="color"
                  value={settings.secondaryColor}
                  onChange={(e) => handleSettingChange('secondaryColor', e.target.value)}
                  inputProps={{ style: { height: 48, padding: 0 } }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Langue"
                  value={settings.language}
                  onChange={(e) => handleSettingChange('language', e.target.value)}
                >
                  <MenuItem value="fr">Français</MenuItem>
                  <MenuItem value="en">English</MenuItem>
                </TextField>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Devise"
                  value={settings.currency}
                  onChange={(e) => handleSettingChange('currency', e.target.value)}
                >
                  <MenuItem value="USD">USD</MenuItem>
                  <MenuItem value="EUR">EUR</MenuItem>
                  <MenuItem value="BTC">BTC</MenuItem>
                </TextField>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Fuseau Horaire"
                  value={settings.timezone}
                  onChange={(e) => handleSettingChange('timezone', e.target.value)}
                >
                  <MenuItem value="Europe/Paris">Europe/Paris</MenuItem>
                  <MenuItem value="America/New_York">America/New_York</MenuItem>
                  <MenuItem value="Asia/Tokyo">Asia/Tokyo</MenuItem>
                </TextField>
              </Grid>
              
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      const preset = { primaryColor: '#00e19d', secondaryColor: '#7aa2f7' }; // Cyber
                      handleSettingChange('primaryColor', preset.primaryColor);
                      handleSettingChange('secondaryColor', preset.secondaryColor);
                      localStorage.setItem('cryptospreadedge-settings', JSON.stringify({ ...settings, ...preset }));
                      const event = new CustomEvent('cryptospreadedge-theme-change', { detail: { mode: settings.theme, ...preset } });
                      window.dispatchEvent(event);
                    }}
                  >
                    Cyber
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      const preset = { primaryColor: '#38bdf8', secondaryColor: '#22c55e' }; // Ocean
                      handleSettingChange('primaryColor', preset.primaryColor);
                      handleSettingChange('secondaryColor', preset.secondaryColor);
                      localStorage.setItem('cryptospreadedge-settings', JSON.stringify({ ...settings, ...preset }));
                      const event = new CustomEvent('cryptospreadedge-theme-change', { detail: { mode: settings.theme, ...preset } });
                      window.dispatchEvent(event);
                    }}
                  >
                    Ocean
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      const preset = { primaryColor: '#00ff5f', secondaryColor: '#00c853' }; // Matrix
                      handleSettingChange('primaryColor', preset.primaryColor);
                      handleSettingChange('secondaryColor', preset.secondaryColor);
                      localStorage.setItem('cryptospreadedge-settings', JSON.stringify({ ...settings, ...preset }));
                      const event = new CustomEvent('cryptospreadedge-theme-change', { detail: { mode: settings.theme, ...preset } });
                      window.dispatchEvent(event);
                    }}
                  >
                    Matrix
                  </Button>
                </Box>
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Intervalle de Rafraîchissement (ms)"
                  type="number"
                  value={settings.refreshInterval}
                  onChange={(e) => handleSettingChange('refreshInterval', parseInt(e.target.value))}
                  inputProps={{ min: 1000, max: 60000, step: 1000 }}
                  helperText="Fréquence de mise à jour des données"
                />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={4}>
            <Typography variant="h6" gutterBottom>
              Système
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Actions Système
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={loadHealthStatus}
                  >
                    Actualiser le Statut
                  </Button>
                  
                  <Button
                    variant="outlined"
                    startIcon={<Save />}
                    onClick={saveSettings}
                    disabled={loading}
                  >
                    Sauvegarder
                  </Button>
                  
                  <Button
                    variant="outlined"
                    color="warning"
                    onClick={resetSettings}
                  >
                    Réinitialiser
                  </Button>
                </Box>
              </Grid>
              
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Zone de Danger
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<Delete />}
                    onClick={() => handleDeleteItem('cache')}
                  >
                    Vider le Cache
                  </Button>
                  
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<Delete />}
                    onClick={() => handleDeleteItem('logs')}
                  >
                    Supprimer les Logs
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </TabPanel>
        </CardContent>
      </Card>

      {/* Dialog de confirmation de suppression */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirmer la Suppression</DialogTitle>
        <DialogContent>
          <Typography>
            Êtes-vous sûr de vouloir supprimer {itemToDelete} ? Cette action est irréversible.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Annuler</Button>
          <Button onClick={confirmDelete} color="error" variant="contained">
            Supprimer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings;