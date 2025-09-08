/**
 * Composant pour le dashboard de performance
 */

import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Typography,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  Refresh as RefreshIcon,
  Error as ErrorIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';
import Sparkline from '../../components/Charts/Sparkline';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { 
  usePerformanceMetrics, 
  usePerformanceSummary,
  useSystemHealth,
  useBackupStatus 
} from '../../hooks/useDatabaseApi';
import ErrorsTrend from './ErrorsTrend';
import ServiceLatencyTable from './ServiceLatencyTable';

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

const PerformanceDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  // const [timeRange, setTimeRange] = useState('24h');

  // Hooks pour les données
  const { data: performanceSummary, loading: summaryLoading } = usePerformanceSummary();
  const { data: systemHealth, loading: healthLoading } = useSystemHealth();
  const { data: backupStatus, loading: backupLoading } = useBackupStatus();
  const { data: performanceMetrics, loading: metricsLoading } = usePerformanceMetrics({
    start_date: format(new Date(Date.now() - 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
    end_date: format(new Date(), 'yyyy-MM-dd'),
  });

  const getSeries = (keys: string[]) => {
    const metrics = (performanceMetrics?.metrics || []) as any[];
    const filtered = metrics.filter(m => {
      const name = String(m.metric_name || '').toLowerCase();
      return keys.some(k => name.includes(k));
    });
    return filtered
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .slice(-20)
      .map((m: any) => ({ value: Number(m.value || 0) }));
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}min`;
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard de Performance
        </Typography>
        <Typography variant="body1" color="textSecondary" gutterBottom>
          Monitoring des performances système et base de données
        </Typography>
      </Box>

      {/* Métriques principales */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Performance générale */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<TrendingUpIcon color="primary" />}
              title="Performance Générale"
              subheader="Score global"
            />
            <CardContent>
              {summaryLoading ? (
                <CircularProgress size={24} />
              ) : performanceSummary ? (
                <Box>
                  <Typography variant="h6" color="primary">
                    {(performanceSummary.overall_score || 0).toFixed(1)}/10
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(performanceSummary.overall_score || 0) * 10}
                    sx={{ mt: 1 }}
                  />
                  <Box sx={{ mt: 1 }}>
                    <Sparkline
                      data={getSeries(['score', 'overall'])}
                      height={36}
                      color="#00e19d"
                    />
                  </Box>
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    Sharpe Ratio: {(performanceSummary.sharpe_ratio || 0).toFixed(2)}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  N/A
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Latence */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<SpeedIcon color="info" />}
              title="Latence Moyenne"
              subheader="Temps de réponse"
            />
            <CardContent>
              {summaryLoading ? (
                <CircularProgress size={24} />
              ) : performanceSummary ? (
                <Box>
                  <Typography variant="h6" color="info.main">
                    {formatDuration(performanceSummary.avg_execution_time || 0)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Max: {formatDuration(performanceSummary.max_execution_time || 0)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Min: {formatDuration(performanceSummary.min_execution_time || 0)}
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Sparkline
                      data={getSeries(['latence', 'latency', 'execution'])}
                      height={36}
                      color="#7aa2f7"
                    />
                  </Box>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  N/A
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Utilisation mémoire */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<MemoryIcon color="warning" />}
              title="Utilisation Mémoire"
              subheader="Base de données"
            />
            <CardContent>
              {healthLoading ? (
                <CircularProgress size={24} />
              ) : systemHealth ? (
                <Box>
                  <Typography variant="h6" color="warning.main">
                    {formatBytes(systemHealth.memory_usage || 0)}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(systemHealth.memory_usage_percent || 0)}
                    sx={{ mt: 1 }}
                  />
                  <Box sx={{ mt: 1 }}>
                    <Sparkline
                      data={getSeries(['memory', 'mémoire', 'ram'])}
                      height={36}
                      color="#f59e0b"
                    />
                  </Box>
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    {systemHealth.memory_usage_percent || 0}% utilisée
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  N/A
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Santé système */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<SecurityIcon color="success" />}
              title="Santé Système"
              subheader="État général"
            />
            <CardContent>
              {healthLoading ? (
                <CircularProgress size={24} />
              ) : systemHealth ? (
                <Box>
                  <Chip
                    label={systemHealth.status || 'Inconnu'}
                    color={getHealthColor(systemHealth.status || '')}
                    size="small"
                  />
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    Connexions: {systemHealth.connections || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Uptime: {systemHealth.uptime || 'N/A'}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  N/A
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Uptime */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<AccessTimeIcon color="success" />}
              title="Uptime"
              subheader="Disponibilité"
            />
            <CardContent>
              {healthLoading ? (
                <CircularProgress size={24} />
              ) : systemHealth ? (
                <Box>
                  <Typography variant="h6" color="success.main">
                    {systemHealth.uptime || 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Services: {systemHealth.connections || 0}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">N/A</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Erreurs / min */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<ErrorIcon color="error" />}
              title="Erreurs / min"
              subheader="Dernières 24h"
            />
            <CardContent>
              {metricsLoading ? (
                <CircularProgress size={24} />
              ) : performanceMetrics ? (
                <Box>
                  <Typography variant="h6" color="error">
                    {(() => {
                      const series = getSeries(['error', 'erreur']);
                      const last = series[series.length - 1]?.value || 0;
                      return last.toFixed(0);
                    })()}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">N/A</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Onglets */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="performance tabs">
            <Tab label="Métriques" icon={<AssessmentIcon />} />
            <Tab label="Requêtes" icon={<SpeedIcon />} />
            <Tab label="Stockage" icon={<StorageIcon />} />
            <Tab label="Backup" icon={<SecurityIcon />} />
            <Tab label="Événements" icon={<RefreshIcon />} />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Métriques de Performance
            </Typography>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} md={6}>
                <ErrorsTrend data={(performanceMetrics?.errors_trend || []).map((e: any) => ({ timestamp: e.timestamp, errorsPerMin: e.value }))} />
              </Grid>
              <Grid item xs={12} md={6}>
                <ServiceLatencyTable
                  items={Object.entries(systemHealth?.services || {}).map(([name, s]: any) => ({ name, status: s.status, response_time: s.response_time }))}
                />
              </Grid>
            </Grid>
            {metricsLoading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : performanceMetrics ? (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Métrique</TableCell>
                      <TableCell>Valeur</TableCell>
                      <TableCell>Unite</TableCell>
                      <TableCell>Timestamp</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {performanceMetrics.metrics?.map((metric: any, index: number) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {metric.metric_name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {metric.value}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {metric.unit || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {metric.timestamp
                              ? format(new Date(metric.timestamp), 'dd/MM/yyyy HH:mm:ss', { locale: fr })
                              : '-'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Alert severity="info">
                Aucune métrique disponible
              </Alert>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Analyse des Requêtes
            </Typography>
            <Alert severity="info">
              Composant d'analyse des requêtes en cours de développement...
            </Alert>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Utilisation du Stockage
            </Typography>
            <Alert severity="info">
              Composant de stockage en cours de développement...
            </Alert>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Statut des Backups
            </Typography>
            {backupLoading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : backupStatus ? (
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardHeader title="Dernier Backup" />
                    <CardContent>
                      <Typography variant="body2">
                        {backupStatus.last_backup 
                          ? format(new Date(backupStatus.last_backup), 'dd/MM/yyyy HH:mm:ss', { locale: fr })
                          : 'Aucun backup'
                        }
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Taille: {backupStatus.last_backup_size ? formatBytes(backupStatus.last_backup_size) : 'N/A'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardHeader title="Prochain Backup" />
                    <CardContent>
                      <Typography variant="body2">
                        {backupStatus.next_backup 
                          ? format(new Date(backupStatus.next_backup), 'dd/MM/yyyy HH:mm:ss', { locale: fr })
                          : 'Non programmé'
                        }
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Fréquence: {backupStatus.backup_frequency || 'N/A'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            ) : (
              <Alert severity="info">
                Aucune information de backup disponible
              </Alert>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Événements Récents
            </Typography>
            {metricsLoading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : performanceMetrics ? (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Message</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(performanceMetrics.events || []).slice(0, 20).map((ev: any, index: number) => (
                      <TableRow key={index}>
                        <TableCell>
                          {ev.timestamp
                            ? format(new Date(ev.timestamp), 'dd/MM/yyyy HH:mm:ss', { locale: fr })
                            : '-'}
                        </TableCell>
                        <TableCell>
                          <Chip label={ev.level?.toUpperCase() || 'INFO'} color={ev.level === 'error' ? 'error' : ev.level === 'warning' ? 'warning' : 'default'} size="small" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" noWrap>
                            {ev.message}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Alert severity="info">Aucun événement</Alert>
            )}
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default PerformanceDashboard;