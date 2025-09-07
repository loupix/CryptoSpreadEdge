/**
 * Composant d'optimisation des performances du frontend
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Typography,
  LinearProgress,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Switch,
  FormControlLabel,
  Slider,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

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
      id={`performance-tabpanel-${index}`}
      aria-labelledby={`performance-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const PerformanceOptimizer: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [performanceMetrics, setPerformanceMetrics] = useState({
    bundleSize: 0,
    loadTime: 0,
    memoryUsage: 0,
    networkRequests: 0,
    cacheHitRate: 0,
    renderTime: 0,
  });
  const [optimizationSettings, setOptimizationSettings] = useState({
    enableLazyLoading: true,
    enableCodeSplitting: true,
    enableImageOptimization: true,
    enableCaching: true,
    enableCompression: true,
    enablePrefetching: false,
    maxCacheSize: 50,
    prefetchThreshold: 1000,
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleSettingChange = (setting: string, value: any) => {
    setOptimizationSettings(prev => ({
      ...prev,
      [setting]: value,
    }));
  };

  const analyzePerformance = async () => {
    setIsAnalyzing(true);
    
    // Simulation d'analyse de performance
    setTimeout(() => {
      setPerformanceMetrics({
        bundleSize: Math.random() * 2 + 1, // MB
        loadTime: Math.random() * 2000 + 500, // ms
        memoryUsage: Math.random() * 100 + 50, // MB
        networkRequests: Math.floor(Math.random() * 50 + 10),
        cacheHitRate: Math.random() * 0.4 + 0.6, // 60-100%
        renderTime: Math.random() * 100 + 10, // ms
      });
      setIsAnalyzing(false);
    }, 2000);
  };

  const getPerformanceColor = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return 'success';
    if (value <= thresholds.warning) return 'warning';
    return 'error';
  };

  const getPerformanceIcon = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return <CheckCircleIcon />;
    if (value <= thresholds.warning) return <WarningIcon />;
    return <ErrorIcon />;
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  useEffect(() => {
    analyzePerformance();
  }, []);

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Optimiseur de Performance
        </Typography>
        <Typography variant="body1" color="textSecondary" gutterBottom>
          Analyse et optimisation des performances du frontend
        </Typography>
      </Box>

      {/* Métriques de performance */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={2}>
          <Card>
            <CardHeader
              avatar={<StorageIcon color="primary" />}
              title="Taille Bundle"
              subheader="JavaScript"
            />
            <CardContent>
              <Typography variant="h6" color="primary">
                {performanceMetrics.bundleSize.toFixed(1)} MB
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(performanceMetrics.bundleSize / 3) * 100}
                color={getPerformanceColor(performanceMetrics.bundleSize, { good: 1.5, warning: 2.5 })}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={2}>
          <Card>
            <CardHeader
              avatar={<SpeedIcon color="info" />}
              title="Temps de Chargement"
              subheader="Initial"
            />
            <CardContent>
              <Typography variant="h6" color="info.main">
                {formatDuration(performanceMetrics.loadTime)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(performanceMetrics.loadTime / 3000) * 100}
                color={getPerformanceColor(performanceMetrics.loadTime, { good: 1000, warning: 2000 })}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={2}>
          <Card>
            <CardHeader
              avatar={<MemoryIcon color="warning" />}
              title="Utilisation Mémoire"
              subheader="RAM"
            />
            <CardContent>
              <Typography variant="h6" color="warning.main">
                {performanceMetrics.memoryUsage.toFixed(0)} MB
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(performanceMetrics.memoryUsage / 200) * 100}
                color={getPerformanceColor(performanceMetrics.memoryUsage, { good: 100, warning: 150 })}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={2}>
          <Card>
            <CardHeader
              avatar={<NetworkIcon color="secondary" />}
              title="Requêtes Réseau"
              subheader="Total"
            />
            <CardContent>
              <Typography variant="h6" color="secondary.main">
                {performanceMetrics.networkRequests}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(performanceMetrics.networkRequests / 100) * 100}
                color={getPerformanceColor(performanceMetrics.networkRequests, { good: 30, warning: 60 })}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={2}>
          <Card>
            <CardHeader
              avatar={<CheckCircleIcon color="success" />}
              title="Taux de Cache"
              subheader="Hit Rate"
            />
            <CardContent>
              <Typography variant="h6" color="success.main">
                {(performanceMetrics.cacheHitRate * 100).toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={performanceMetrics.cacheHitRate * 100}
                color={getPerformanceColor(performanceMetrics.cacheHitRate, { good: 0.8, warning: 0.6 })}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={2}>
          <Card>
            <CardHeader
              avatar={<SpeedIcon color="error" />}
              title="Temps de Rendu"
              subheader="Moyen"
            />
            <CardContent>
              <Typography variant="h6" color="error.main">
                {formatDuration(performanceMetrics.renderTime)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(performanceMetrics.renderTime / 200) * 100}
                color={getPerformanceColor(performanceMetrics.renderTime, { good: 50, warning: 100 })}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Bouton d'analyse */}
      <Box display="flex" justifyContent="center" mb={3}>
        <Button
          variant="contained"
          startIcon={isAnalyzing ? <CircularProgress size={20} /> : <RefreshIcon />}
          onClick={analyzePerformance}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? 'Analyse en cours...' : 'Analyser les Performances'}
        </Button>
      </Box>

      {/* Onglets */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="performance tabs">
            <Tab label="Recommandations" icon={<SettingsIcon />} />
            <Tab label="Paramètres" icon={<SettingsIcon />} />
            <Tab label="Analyse Détaillée" icon={<SpeedIcon />} />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Recommandations d'Optimisation
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">
                      Optimisation du Bundle
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="body2" gutterBottom>
                        Taille actuelle: {performanceMetrics.bundleSize.toFixed(1)} MB
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        Recommandations:
                      </Typography>
                      <ul>
                        <li>Activer le code splitting</li>
                        <li>Utiliser le lazy loading</li>
                        <li>Minifier le code JavaScript</li>
                        <li>Supprimer les dépendances inutilisées</li>
                      </ul>
                    </Box>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">
                      Optimisation du Chargement
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="body2" gutterBottom>
                        Temps actuel: {formatDuration(performanceMetrics.loadTime)}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        Recommandations:
                      </Typography>
                      <ul>
                        <li>Optimiser les images</li>
                        <li>Utiliser le CDN</li>
                        <li>Activer la compression Gzip</li>
                        <li>Précharger les ressources critiques</li>
                      </ul>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              </Grid>

              <Grid item xs={12} md={6}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">
                      Optimisation de la Mémoire
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="body2" gutterBottom>
                        Utilisation actuelle: {performanceMetrics.memoryUsage.toFixed(0)} MB
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        Recommandations:
                      </Typography>
                      <ul>
                        <li>Implémenter la pagination</li>
                        <li>Utiliser la virtualisation</li>
                        <li>Nettoyer les event listeners</li>
                        <li>Optimiser les re-renders</li>
                      </ul>
                    </Box>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">
                      Optimisation du Cache
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="body2" gutterBottom>
                        Taux actuel: {(performanceMetrics.cacheHitRate * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        Recommandations:
                      </Typography>
                      <ul>
                        <li>Configurer les headers de cache</li>
                        <li>Utiliser Service Workers</li>
                        <li>Implémenter le cache local</li>
                        <li>Optimiser les stratégies de cache</li>
                      </ul>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Paramètres d'Optimisation
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Chargement" />
                  <CardContent>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={optimizationSettings.enableLazyLoading}
                          onChange={(e) => handleSettingChange('enableLazyLoading', e.target.checked)}
                        />
                      }
                      label="Lazy Loading activé"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={optimizationSettings.enableCodeSplitting}
                          onChange={(e) => handleSettingChange('enableCodeSplitting', e.target.checked)}
                        />
                      }
                      label="Code Splitting activé"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={optimizationSettings.enableImageOptimization}
                          onChange={(e) => handleSettingChange('enableImageOptimization', e.target.checked)}
                        />
                      }
                      label="Optimisation des images"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={optimizationSettings.enablePrefetching}
                          onChange={(e) => handleSettingChange('enablePrefetching', e.target.checked)}
                        />
                      }
                      label="Préchargement intelligent"
                    />
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Cache" />
                  <CardContent>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={optimizationSettings.enableCaching}
                          onChange={(e) => handleSettingChange('enableCaching', e.target.checked)}
                        />
                      }
                      label="Cache activé"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={optimizationSettings.enableCompression}
                          onChange={(e) => handleSettingChange('enableCompression', e.target.checked)}
                        />
                      }
                      label="Compression activée"
                    />
                    
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Taille maximale du cache (MB)
                      </Typography>
                      <Slider
                        value={optimizationSettings.maxCacheSize}
                        onChange={(e, value) => handleSettingChange('maxCacheSize', value)}
                        min={10}
                        max={200}
                        step={10}
                        marks={[
                          { value: 10, label: '10MB' },
                          { value: 50, label: '50MB' },
                          { value: 100, label: '100MB' },
                          { value: 200, label: '200MB' },
                        ]}
                        valueLabelDisplay="auto"
                      />
                    </Box>

                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Seuil de préchargement (ms)
                      </Typography>
                      <TextField
                        type="number"
                        value={optimizationSettings.prefetchThreshold}
                        onChange={(e) => handleSettingChange('prefetchThreshold', parseInt(e.target.value))}
                        fullWidth
                        inputProps={{ min: 100, max: 5000, step: 100 }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Analyse Détaillée des Performances
            </Typography>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Métrique</TableCell>
                    <TableCell>Valeur Actuelle</TableCell>
                    <TableCell>Seuil Optimal</TableCell>
                    <TableCell>Statut</TableCell>
                    <TableCell>Impact</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Taille du Bundle</TableCell>
                    <TableCell>{performanceMetrics.bundleSize.toFixed(1)} MB</TableCell>
                    <TableCell>&lt; 1.5 MB</TableCell>
                    <TableCell>
                      <Chip
                        icon={getPerformanceIcon(performanceMetrics.bundleSize, { good: 1.5, warning: 2.5 })}
                        label={performanceMetrics.bundleSize <= 1.5 ? 'Optimal' : performanceMetrics.bundleSize <= 2.5 ? 'Acceptable' : 'Critique'}
                        color={getPerformanceColor(performanceMetrics.bundleSize, { good: 1.5, warning: 2.5 })}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Élevé</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Temps de Chargement</TableCell>
                    <TableCell>{formatDuration(performanceMetrics.loadTime)}</TableCell>
                    <TableCell>&lt; 1s</TableCell>
                    <TableCell>
                      <Chip
                        icon={getPerformanceIcon(performanceMetrics.loadTime, { good: 1000, warning: 2000 })}
                        label={performanceMetrics.loadTime <= 1000 ? 'Optimal' : performanceMetrics.loadTime <= 2000 ? 'Acceptable' : 'Critique'}
                        color={getPerformanceColor(performanceMetrics.loadTime, { good: 1000, warning: 2000 })}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Très Élevé</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Utilisation Mémoire</TableCell>
                    <TableCell>{performanceMetrics.memoryUsage.toFixed(0)} MB</TableCell>
                    <TableCell>&lt; 100 MB</TableCell>
                    <TableCell>
                      <Chip
                        icon={getPerformanceIcon(performanceMetrics.memoryUsage, { good: 100, warning: 150 })}
                        label={performanceMetrics.memoryUsage <= 100 ? 'Optimal' : performanceMetrics.memoryUsage <= 150 ? 'Acceptable' : 'Critique'}
                        color={getPerformanceColor(performanceMetrics.memoryUsage, { good: 100, warning: 150 })}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Moyen</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Requêtes Réseau</TableCell>
                    <TableCell>{performanceMetrics.networkRequests}</TableCell>
                    <TableCell>&lt; 30</TableCell>
                    <TableCell>
                      <Chip
                        icon={getPerformanceIcon(performanceMetrics.networkRequests, { good: 30, warning: 60 })}
                        label={performanceMetrics.networkRequests <= 30 ? 'Optimal' : performanceMetrics.networkRequests <= 60 ? 'Acceptable' : 'Critique'}
                        color={getPerformanceColor(performanceMetrics.networkRequests, { good: 30, warning: 60 })}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Élevé</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Taux de Cache</TableCell>
                    <TableCell>{(performanceMetrics.cacheHitRate * 100).toFixed(1)}%</TableCell>
                    <TableCell>&gt; 80%</TableCell>
                    <TableCell>
                      <Chip
                        icon={getPerformanceIcon(performanceMetrics.cacheHitRate, { good: 0.8, warning: 0.6 })}
                        label={performanceMetrics.cacheHitRate >= 0.8 ? 'Optimal' : performanceMetrics.cacheHitRate >= 0.6 ? 'Acceptable' : 'Critique'}
                        color={getPerformanceColor(performanceMetrics.cacheHitRate, { good: 0.8, warning: 0.6 })}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Moyen</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Temps de Rendu</TableCell>
                    <TableCell>{formatDuration(performanceMetrics.renderTime)}</TableCell>
                    <TableCell>&lt; 50ms</TableCell>
                    <TableCell>
                      <Chip
                        icon={getPerformanceIcon(performanceMetrics.renderTime, { good: 50, warning: 100 })}
                        label={performanceMetrics.renderTime <= 50 ? 'Optimal' : performanceMetrics.renderTime <= 100 ? 'Acceptable' : 'Critique'}
                        color={getPerformanceColor(performanceMetrics.renderTime, { good: 50, warning: 100 })}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Élevé</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default PerformanceOptimizer;