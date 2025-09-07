// Types pour la navigation
export type RootStackParamList = {
  Login: undefined;
  Register: undefined;
  Main: undefined;
  Profile: undefined;
};

export type MainTabParamList = {
  Dashboard: undefined;
  Trading: undefined;
  Portfolio: undefined;
  Arbitrage: undefined;
  Settings: undefined;
};

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

export type MainStackParamList = {
  MainTabs: undefined;
  Profile: undefined;
  TradingDetails: { symbol: string };
  PortfolioDetails: { positionId: string };
  ArbitrageDetails: { opportunityId: string };
  Settings: undefined;
  Notifications: undefined;
  Alerts: undefined;
};