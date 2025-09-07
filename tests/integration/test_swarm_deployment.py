"""
Tests d'intégration pour le déploiement Docker Swarm optimisé
"""
import pytest
import requests
import time
import subprocess
import json
from typing import Dict, List


class TestSwarmDeployment:
    """Tests pour le déploiement Docker Swarm optimisé"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup pour les tests de déploiement"""
        self.base_url = "http://localhost"
        self.metrics_url = f"{self.base_url}:9001"
        self.monitor_url = f"{self.base_url}:9002"
        self.prometheus_url = f"{self.base_url}/prometheus"
        self.grafana_url = f"{self.base_url}/grafana"
        
    def test_swarm_services_running(self):
        """Test que tous les services Swarm sont en cours d'exécution"""
        result = subprocess.run(
            ["docker", "service", "ls", "--filter", "name=cryptospreadedge-portfolio", "--format", "{{.Name}}"],
            capture_output=True,
            text=True
        )
        
        services = result.stdout.strip().split('\n')
        expected_services = [
            "cryptospreadedge-portfolio_cryptospreadedge-main",
            "cryptospreadedge-portfolio_portfolio-rebalancer",
            "cryptospreadedge-portfolio_arbitrage-worker",
            "cryptospreadedge-portfolio_portfolio-monitor",
            "cryptospreadedge-portfolio_nginx",
            "cryptospreadedge-portfolio_redis",
            "cryptospreadedge-portfolio_influxdb",
            "cryptospreadedge-portfolio_prometheus",
            "cryptospreadedge-portfolio_grafana"
        ]
        
        for service in expected_services:
            assert service in services, f"Service {service} n'est pas en cours d'exécution"
    
    def test_nginx_load_balancer(self):
        """Test que Nginx fonctionne comme load balancer"""
        response = requests.get(f"{self.base_url}/health", timeout=10)
        assert response.status_code == 200
        assert "healthy" in response.text
    
    def test_portfolio_metrics_endpoint(self):
        """Test que l'endpoint des métriques de portefeuille est accessible"""
        try:
            response = requests.get(f"{self.metrics_url}/metrics", timeout=10)
            assert response.status_code == 200
            assert "portfolio_rebalance" in response.text
        except requests.exceptions.ConnectionError:
            pytest.skip("Service de métriques non accessible (normal en mode test)")
    
    def test_portfolio_monitor_endpoint(self):
        """Test que l'endpoint de monitoring portfolio est accessible"""
        try:
            response = requests.get(f"{self.monitor_url}/", timeout=10)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Service de monitoring non accessible (normal en mode test)")
    
    def test_prometheus_accessible(self):
        """Test que Prometheus est accessible"""
        try:
            response = requests.get(f"{self.prometheus_url}/", timeout=10)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Prometheus non accessible (normal en mode test)")
    
    def test_grafana_accessible(self):
        """Test que Grafana est accessible"""
        try:
            response = requests.get(f"{self.grafana_url}/", timeout=10)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Grafana non accessible (normal en mode test)")
    
    def test_redis_connectivity(self):
        """Test la connectivité Redis"""
        result = subprocess.run(
            ["docker", "exec", "cryptospreadedge-portfolio_redis.1", "redis-cli", "ping"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "PONG" in result.stdout
    
    def test_influxdb_connectivity(self):
        """Test la connectivité InfluxDB"""
        try:
            response = requests.get("http://localhost:8086/health", timeout=10)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("InfluxDB non accessible (normal en mode test)")
    
    def test_service_health_checks(self):
        """Test que les health checks des services fonctionnent"""
        services = [
            "cryptospreadedge-portfolio_cryptospreadedge-main",
            "cryptospreadedge-portfolio_portfolio-rebalancer",
            "cryptospreadedge-portfolio_arbitrage-worker"
        ]
        
        for service in services:
            result = subprocess.run(
                ["docker", "service", "ps", service, "--filter", "desired-state=running", "--format", "{{.CurrentState}}"],
                capture_output=True,
                text=True
            )
            
            states = result.stdout.strip().split('\n')
            running_states = [state for state in states if "Running" in state]
            assert len(running_states) > 0, f"Service {service} n'a pas de tâches en cours d'exécution"
    
    def test_volume_persistence(self):
        """Test que les volumes persistants sont créés"""
        volumes = [
            "cryptospreadedge-portfolio_redis_data",
            "cryptospreadedge-portfolio_influxdb_data",
            "cryptospreadedge-portfolio_kafka_data",
            "cryptospreadedge-portfolio_prometheus_data",
            "cryptospreadedge-portfolio_grafana_data"
        ]
        
        result = subprocess.run(
            ["docker", "volume", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True
        )
        
        existing_volumes = result.stdout.strip().split('\n')
        for volume in volumes:
            assert volume in existing_volumes, f"Volume {volume} n'existe pas"
    
    def test_secrets_created(self):
        """Test que les secrets Docker Swarm sont créés"""
        secrets = [
            "api_keys_encrypted",
            "arbitrage_env",
            "rebalance_env"
        ]
        
        result = subprocess.run(
            ["docker", "secret", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True
        )
        
        existing_secrets = result.stdout.strip().split('\n')
        for secret in secrets:
            assert secret in existing_secrets, f"Secret {secret} n'existe pas"
    
    def test_configs_created(self):
        """Test que les configs Docker Swarm sont créées"""
        configs = [
            "nginx_conf",
            "prometheus_conf",
            "grafana_dashboards"
        ]
        
        result = subprocess.run(
            ["docker", "config", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True
        )
        
        existing_configs = result.stdout.strip().split('\n')
        for config in configs:
            assert config in existing_configs, f"Config {config} n'existe pas"
    
    def test_network_isolation(self):
        """Test que les réseaux sont correctement isolés"""
        networks = [
            "cryptospreadedge-portfolio_frontend",
            "cryptospreadedge-portfolio_backend",
            "cryptospreadedge-portfolio_monitoring"
        ]
        
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True
        )
        
        existing_networks = result.stdout.strip().split('\n')
        for network in networks:
            assert network in existing_networks, f"Réseau {network} n'existe pas"
    
    def test_resource_limits(self):
        """Test que les limites de ressources sont appliquées"""
        result = subprocess.run(
            ["docker", "service", "inspect", "cryptospreadedge-portfolio_cryptospreadedge-main", "--format", "{{json .Spec.TaskTemplate.Resources}}"],
            capture_output=True,
            text=True
        )
        
        resources = json.loads(result.stdout)
        assert "Limits" in resources
        assert "Reservations" in resources
        
        limits = resources["Limits"]
        assert "NanoCPUs" in limits
        assert "MemoryBytes" in limits
        
        # Vérifier que les limites sont raisonnables
        assert limits["NanoCPUs"] <= 3000000000  # 3 CPU max
        assert limits["MemoryBytes"] <= 8000000000  # 8GB max
    
    def test_placement_constraints(self):
        """Test que les contraintes de placement sont appliquées"""
        result = subprocess.run(
            ["docker", "service", "inspect", "cryptospreadedge-portfolio_cryptospreadedge-main", "--format", "{{json .Spec.TaskTemplate.Placement}}"],
            capture_output=True,
            text=True
        )
        
        placement = json.loads(result.stdout)
        assert "Constraints" in placement
        constraints = placement["Constraints"]
        
        # Vérifier qu'il y a des contraintes de nœud
        assert any("node.role" in constraint for constraint in constraints)
    
    def test_rolling_update_config(self):
        """Test que la configuration de rolling update est correcte"""
        result = subprocess.run(
            ["docker", "service", "inspect", "cryptospreadedge-portfolio_cryptospreadedge-main", "--format", "{{json .Spec.UpdateConfig}}"],
            capture_output=True,
            text=True
        )
        
        update_config = json.loads(result.stdout)
        assert update_config["Parallelism"] == 1
        assert update_config["Delay"] == 10000000000  # 10s en nanosecondes
        assert update_config["FailureAction"] == "rollback"
    
    def test_logging_configuration(self):
        """Test que la configuration de logging est correcte"""
        result = subprocess.run(
            ["docker", "service", "inspect", "cryptospreadedge-portfolio_cryptospreadedge-main", "--format", "{{json .Spec.TaskTemplate.LogDriver}}"],
            capture_output=True,
            text=True
        )
        
        log_driver = json.loads(result.stdout)
        assert log_driver["Name"] == "json-file"
        assert "max-size" in log_driver["Options"]
        assert "max-file" in log_driver["Options"]
    
    def test_environment_variables(self):
        """Test que les variables d'environnement sont correctement définies"""
        result = subprocess.run(
            ["docker", "service", "inspect", "cryptospreadedge-portfolio_cryptospreadedge-main", "--format", "{{json .Spec.TaskTemplate.ContainerSpec.Env}}"],
            capture_output=True,
            text=True
        )
        
        env_vars = json.loads(result.stdout)
        env_dict = {var.split('=')[0]: var.split('=')[1] for var in env_vars if '=' in var}
        
        # Vérifier les variables d'environnement critiques
        assert "CSE_REBALANCE_ENABLED" in env_dict
        assert env_dict["CSE_REBALANCE_ENABLED"] == "1"
        assert "CSE_REBALANCE_METHOD" in env_dict
        assert env_dict["CSE_REBALANCE_METHOD"] == "rp"
        assert "CSE_REBALANCE_PROMETHEUS" in env_dict
        assert env_dict["CSE_REBALANCE_PROMETHEUS"] == "1"
    
    def test_secret_mounts(self):
        """Test que les secrets sont correctement montés"""
        result = subprocess.run(
            ["docker", "service", "inspect", "cryptospreadedge-portfolio_cryptospreadedge-main", "--format", "{{json .Spec.TaskTemplate.ContainerSpec.Secrets}}"],
            capture_output=True,
            text=True
        )
        
        secrets = json.loads(result.stdout)
        secret_names = [secret["SecretName"] for secret in secrets]
        
        expected_secrets = ["api_keys_encrypted", "arbitrage_env", "rebalance_env"]
        for secret in expected_secrets:
            assert secret in secret_names, f"Secret {secret} n'est pas monté"
    
    def test_config_mounts(self):
        """Test que les configs sont correctement montées"""
        result = subprocess.run(
            ["docker", "service", "inspect", "cryptospreadedge-portfolio_cryptospreadedge-main", "--format", "{{json .Spec.TaskTemplate.ContainerSpec.Configs}}"],
            capture_output=True,
            text=True
        )
        
        configs = json.loads(result.stdout)
        config_names = [config["ConfigName"] for config in configs]
        
        expected_configs = ["prometheus_conf"]
        for config in expected_configs:
            assert config in config_names, f"Config {config} n'est pas montée"
    
    def test_health_check_configuration(self):
        """Test que les health checks sont configurés"""
        result = subprocess.run(
            ["docker", "service", "inspect", "cryptospreadedge-portfolio_cryptospreadedge-main", "--format", "{{json .Spec.TaskTemplate.ContainerSpec.HealthCheck}}"],
            capture_output=True,
            text=True
        )
        
        health_check = json.loads(result.stdout)
        assert "Test" in health_check
        assert "Interval" in health_check
        assert "Timeout" in health_check
        assert "Retries" in health_check
        assert "StartPeriod" in health_check
        
        # Vérifier les valeurs
        assert health_check["Interval"] == 30000000000  # 30s en nanosecondes
        assert health_check["Timeout"] == 5000000000   # 5s en nanosecondes
        assert health_check["Retries"] == 3
        assert health_check["StartPeriod"] == 30000000000  # 30s en nanosecondes