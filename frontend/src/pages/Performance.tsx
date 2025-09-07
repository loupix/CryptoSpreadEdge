/**
 * Page de monitoring des performances
 */

import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Paper,
  Typography,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import PerformanceDashboard from '../components/Performance/PerformanceDashboard';
import PerformanceOptimizer from '../components/Performance/PerformanceOptimizer';

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

const Performance: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Performance & Monitoring
        </Typography>
        <Typography variant="body1" color="textSecondary" gutterBottom>
          Surveillance des performances système et optimisation du frontend
        </Typography>
      </Box>

      {/* Onglets */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="performance tabs">
            <Tab label="Dashboard" icon={<SpeedIcon />} />
            <Tab label="Optimiseur" icon={<SettingsIcon />} />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <PerformanceDashboard />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <PerformanceOptimizer />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default Performance;