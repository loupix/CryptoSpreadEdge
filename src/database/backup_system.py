"""
Système de backup et de réplication avancé pour CryptoSpreadEdge
"""

import asyncio
import logging
import os
import shutil
import gzip
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid
import subprocess
import tempfile
from pathlib import Path

from .database import get_database_manager
from .extended_models import Base

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Types de backup"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"


class BackupStatus(Enum):
    """Statut des backups"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CompressionType(Enum):
    """Types de compression"""
    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    LZ4 = "lz4"
    ZSTD = "zstd"


@dataclass
class BackupConfig:
    """Configuration de backup"""
    name: str
    backup_type: BackupType
    compression: CompressionType = CompressionType.GZIP
    retention_days: int = 30
    schedule: str = "0 2 * * *"  # Cron format
    enabled: bool = True
    tables: List[str] = None  # Tables spécifiques, None = toutes
    exclude_tables: List[str] = None
    parallel_jobs: int = 4
    chunk_size: int = 1000
    metadata: Dict[str, Any] = None


@dataclass
class BackupResult:
    """Résultat d'un backup"""
    backup_id: str
    config_name: str
    status: BackupStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    compressed_size: Optional[int] = None
    tables_backed_up: List[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class BackupSystem:
    """Système de backup et de réplication"""
    
    def __init__(self, db_manager, backup_dir: str = "backups"):
        self.db_manager = db_manager
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.configs: Dict[str, BackupConfig] = {}
        self.results: Dict[str, BackupResult] = {}
        self.is_running = False
        
        self._load_default_configs()
    
    def _load_default_configs(self):
        """Charge les configurations de backup par défaut"""
        
        # Backup complet quotidien
        self.configs["daily_full"] = BackupConfig(
            name="daily_full",
            backup_type=BackupType.FULL,
            compression=CompressionType.GZIP,
            retention_days=30,
            schedule="0 2 * * *",
            enabled=True,
            parallel_jobs=4
        )
        
        # Backup incrémental horaire
        self.configs["hourly_incremental"] = BackupConfig(
            name="hourly_incremental",
            backup_type=BackupType.INCREMENTAL,
            compression=CompressionType.GZIP,
            retention_days=7,
            schedule="0 * * * *",
            enabled=True,
            parallel_jobs=2
        )
        
        # Backup des données critiques uniquement
        self.configs["critical_data"] = BackupConfig(
            name="critical_data",
            backup_type=BackupType.DATA_ONLY,
            compression=CompressionType.ZSTD,
            retention_days=90,
            schedule="0 1 * * *",
            enabled=True,
            tables=["orders", "positions", "trades", "users"],
            parallel_jobs=2
        )
        
        # Backup du schéma uniquement
        self.configs["schema_only"] = BackupConfig(
            name="schema_only",
            backup_type=BackupType.SCHEMA_ONLY,
            compression=CompressionType.GZIP,
            retention_days=365,
            schedule="0 0 1 * *",  # Mensuel
            enabled=True
        )
    
    async def start(self):
        """Démarre le système de backup"""
        self.is_running = True
        logger.info("Système de backup démarré")
        
        # Démarrer les tâches de backup
        asyncio.create_task(self._backup_scheduler_loop())
        asyncio.create_task(self._cleanup_loop())
        asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        """Arrête le système de backup"""
        self.is_running = False
        logger.info("Système de backup arrêté")
    
    async def _backup_scheduler_loop(self):
        """Boucle de planification des backups"""
        while self.is_running:
            try:
                # Vérifier les backups programmés
                await self._check_scheduled_backups()
                
                # Attendre avant la prochaine vérification
                await asyncio.sleep(60)  # Vérifier toutes les minutes
                
            except Exception as e:
                logger.error(f"Erreur planificateur backup: {e}")
                await asyncio.sleep(300)
    
    async def _check_scheduled_backups(self):
        """Vérifie les backups programmés"""
        try:
            current_time = datetime.utcnow()
            
            for config_name, config in self.configs.items():
                if not config.enabled:
                    continue
                
                # Vérifier si le backup doit être exécuté
                if await self._should_run_backup(config, current_time):
                    await self._execute_backup(config)
                    
        except Exception as e:
            logger.error(f"Erreur vérification backups programmés: {e}")
    
    async def _should_run_backup(self, config: BackupConfig, current_time: datetime) -> bool:
        """Détermine si un backup doit être exécuté"""
        try:
            # Vérifier le dernier backup
            last_backup = await self._get_last_backup(config.name)
            
            if not last_backup:
                return True
            
            # Vérifier l'intervalle selon le type
            if config.backup_type == BackupType.FULL:
                # Backup complet quotidien
                return (current_time - last_backup.start_time).days >= 1
            elif config.backup_type == BackupType.INCREMENTAL:
                # Backup incrémental horaire
                return (current_time - last_backup.start_time).hours >= 1
            elif config.backup_type == BackupType.DIFFERENTIAL:
                # Backup différentiel toutes les 6 heures
                return (current_time - last_backup.start_time).hours >= 6
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur vérification backup {config.name}: {e}")
            return False
    
    async def _get_last_backup(self, config_name: str) -> Optional[BackupResult]:
        """Récupère le dernier backup d'une configuration"""
        try:
            # Chercher dans les résultats
            config_backups = [r for r in self.results.values() if r.config_name == config_name]
            
            if not config_backups:
                return None
            
            # Retourner le plus récent
            return max(config_backups, key=lambda x: x.start_time)
            
        except Exception as e:
            logger.error(f"Erreur récupération dernier backup {config_name}: {e}")
            return None
    
    async def _execute_backup(self, config: BackupConfig):
        """Exécute un backup"""
        backup_id = str(uuid.uuid4())
        
        try:
            # Créer le résultat de backup
            result = BackupResult(
                backup_id=backup_id,
                config_name=config.name,
                status=BackupStatus.IN_PROGRESS,
                start_time=datetime.utcnow(),
                tables_backed_up=[],
                metadata={}
            )
            
            self.results[backup_id] = result
            
            logger.info(f"Démarrage backup {config.name} (ID: {backup_id})")
            
            # Exécuter le backup selon le type
            if config.backup_type == BackupType.FULL:
                await self._execute_full_backup(config, result)
            elif config.backup_type == BackupType.INCREMENTAL:
                await self._execute_incremental_backup(config, result)
            elif config.backup_type == BackupType.DIFFERENTIAL:
                await self._execute_differential_backup(config, result)
            elif config.backup_type == BackupType.SCHEMA_ONLY:
                await self._execute_schema_backup(config, result)
            elif config.backup_type == BackupType.DATA_ONLY:
                await self._execute_data_backup(config, result)
            
            # Marquer comme terminé
            result.status = BackupStatus.COMPLETED
            result.end_time = datetime.utcnow()
            
            logger.info(f"Backup {config.name} terminé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur exécution backup {config.name}: {e}")
            
            if backup_id in self.results:
                self.results[backup_id].status = BackupStatus.FAILED
                self.results[backup_id].error_message = str(e)
                self.results[backup_id].end_time = datetime.utcnow()
    
    async def _execute_full_backup(self, config: BackupConfig, result: BackupResult):
        """Exécute un backup complet"""
        try:
            # Générer le nom de fichier
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.name}_full_{timestamp}.sql"
            filepath = self.backup_dir / filename
            
            # Exécuter pg_dump
            cmd = [
                "pg_dump",
                "-h", "localhost",
                "-U", "trading_user",
                "-d", "cryptospreadedge",
                "-f", str(filepath),
                "--verbose",
                "--no-password"
            ]
            
            # Ajouter les options selon la configuration
            if config.tables:
                cmd.extend(["-t", ",".join(config.tables)])
            
            if config.exclude_tables:
                for table in config.exclude_tables:
                    cmd.extend(["--exclude-table", table])
            
            # Exécuter la commande
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erreur pg_dump: {stderr.decode()}")
            
            # Compresser si nécessaire
            if config.compression != CompressionType.NONE:
                compressed_path = await self._compress_file(filepath, config.compression)
                result.file_path = str(compressed_path)
                result.compressed_size = compressed_path.stat().st_size
                
                # Supprimer le fichier non compressé
                filepath.unlink()
            else:
                result.file_path = str(filepath)
            
            result.file_size = filepath.stat().st_size if filepath.exists() else result.compressed_size
            
        except Exception as e:
            logger.error(f"Erreur backup complet: {e}")
            raise
    
    async def _execute_incremental_backup(self, config: BackupConfig, result: BackupResult):
        """Exécute un backup incrémental"""
        try:
            # Récupérer la date du dernier backup
            last_backup = await self._get_last_backup(config.name)
            
            if not last_backup:
                # Pas de backup précédent, faire un backup complet
                await self._execute_full_backup(config, result)
                return
            
            # Générer le nom de fichier
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.name}_incremental_{timestamp}.sql"
            filepath = self.backup_dir / filename
            
            # Exécuter pg_dump avec filtre de date
            cmd = [
                "pg_dump",
                "-h", "localhost",
                "-U", "trading_user",
                "-d", "cryptospreadedge",
                "-f", str(filepath),
                "--verbose",
                "--no-password",
                "--where", f"updated_at > '{last_backup.start_time.isoformat()}'"
            ]
            
            # Exécuter la commande
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erreur pg_dump incrémental: {stderr.decode()}")
            
            # Compresser si nécessaire
            if config.compression != CompressionType.NONE:
                compressed_path = await self._compress_file(filepath, config.compression)
                result.file_path = str(compressed_path)
                result.compressed_size = compressed_path.stat().st_size
                
                # Supprimer le fichier non compressé
                filepath.unlink()
            else:
                result.file_path = str(filepath)
            
            result.file_size = filepath.stat().st_size if filepath.exists() else result.compressed_size
            
        except Exception as e:
            logger.error(f"Erreur backup incrémental: {e}")
            raise
    
    async def _execute_differential_backup(self, config: BackupConfig, result: BackupResult):
        """Exécute un backup différentiel"""
        try:
            # Récupérer la date du dernier backup complet
            last_full_backup = await self._get_last_full_backup(config.name)
            
            if not last_full_backup:
                # Pas de backup complet, faire un backup complet
                await self._execute_full_backup(config, result)
                return
            
            # Générer le nom de fichier
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.name}_differential_{timestamp}.sql"
            filepath = self.backup_dir / filename
            
            # Exécuter pg_dump avec filtre de date
            cmd = [
                "pg_dump",
                "-h", "localhost",
                "-U", "trading_user",
                "-d", "cryptospreadedge",
                "-f", str(filepath),
                "--verbose",
                "--no-password",
                "--where", f"updated_at > '{last_full_backup.start_time.isoformat()}'"
            ]
            
            # Exécuter la commande
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erreur pg_dump différentiel: {stderr.decode()}")
            
            # Compresser si nécessaire
            if config.compression != CompressionType.NONE:
                compressed_path = await self._compress_file(filepath, config.compression)
                result.file_path = str(compressed_path)
                result.compressed_size = compressed_path.stat().st_size
                
                # Supprimer le fichier non compressé
                filepath.unlink()
            else:
                result.file_path = str(filepath)
            
            result.file_size = filepath.stat().st_size if filepath.exists() else result.compressed_size
            
        except Exception as e:
            logger.error(f"Erreur backup différentiel: {e}")
            raise
    
    async def _get_last_full_backup(self, config_name: str) -> Optional[BackupResult]:
        """Récupère le dernier backup complet"""
        try:
            # Chercher dans les résultats
            config_backups = [
                r for r in self.results.values() 
                if r.config_name == config_name and r.status == BackupStatus.COMPLETED
            ]
            
            if not config_backups:
                return None
            
            # Retourner le plus récent
            return max(config_backups, key=lambda x: x.start_time)
            
        except Exception as e:
            logger.error(f"Erreur récupération dernier backup complet {config_name}: {e}")
            return None
    
    async def _execute_schema_backup(self, config: BackupConfig, result: BackupResult):
        """Exécute un backup du schéma uniquement"""
        try:
            # Générer le nom de fichier
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.name}_schema_{timestamp}.sql"
            filepath = self.backup_dir / filename
            
            # Exécuter pg_dump pour le schéma uniquement
            cmd = [
                "pg_dump",
                "-h", "localhost",
                "-U", "trading_user",
                "-d", "cryptospreadedge",
                "-f", str(filepath),
                "--verbose",
                "--no-password",
                "--schema-only",
                "--no-owner",
                "--no-privileges"
            ]
            
            # Exécuter la commande
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erreur pg_dump schéma: {stderr.decode()}")
            
            # Compresser si nécessaire
            if config.compression != CompressionType.NONE:
                compressed_path = await self._compress_file(filepath, config.compression)
                result.file_path = str(compressed_path)
                result.compressed_size = compressed_path.stat().st_size
                
                # Supprimer le fichier non compressé
                filepath.unlink()
            else:
                result.file_path = str(filepath)
            
            result.file_size = filepath.stat().st_size if filepath.exists() else result.compressed_size
            
        except Exception as e:
            logger.error(f"Erreur backup schéma: {e}")
            raise
    
    async def _execute_data_backup(self, config: BackupConfig, result: BackupResult):
        """Exécute un backup des données uniquement"""
        try:
            # Générer le nom de fichier
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.name}_data_{timestamp}.sql"
            filepath = self.backup_dir / filename
            
            # Exécuter pg_dump pour les données uniquement
            cmd = [
                "pg_dump",
                "-h", "localhost",
                "-U", "trading_user",
                "-d", "cryptospreadedge",
                "-f", str(filepath),
                "--verbose",
                "--no-password",
                "--data-only",
                "--disable-triggers"
            ]
            
            # Ajouter les tables spécifiques
            if config.tables:
                cmd.extend(["-t", ",".join(config.tables)])
            
            # Exécuter la commande
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erreur pg_dump données: {stderr.decode()}")
            
            # Compresser si nécessaire
            if config.compression != CompressionType.NONE:
                compressed_path = await self._compress_file(filepath, config.compression)
                result.file_path = str(compressed_path)
                result.compressed_size = compressed_path.stat().st_size
                
                # Supprimer le fichier non compressé
                filepath.unlink()
            else:
                result.file_path = str(filepath)
            
            result.file_size = filepath.stat().st_size if filepath.exists() else result.compressed_size
            
        except Exception as e:
            logger.error(f"Erreur backup données: {e}")
            raise
    
    async def _compress_file(self, filepath: Path, compression: CompressionType) -> Path:
        """Compresse un fichier"""
        try:
            if compression == CompressionType.GZIP:
                compressed_path = filepath.with_suffix(filepath.suffix + '.gz')
                with open(filepath, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                return compressed_path
            
            elif compression == CompressionType.BZIP2:
                compressed_path = filepath.with_suffix(filepath.suffix + '.bz2')
                cmd = ['bzip2', '-c', str(filepath)]
                with open(compressed_path, 'wb') as f_out:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=f_out,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                return compressed_path
            
            elif compression == CompressionType.LZ4:
                compressed_path = filepath.with_suffix(filepath.suffix + '.lz4')
                cmd = ['lz4', '-c', str(filepath)]
                with open(compressed_path, 'wb') as f_out:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=f_out,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                return compressed_path
            
            elif compression == CompressionType.ZSTD:
                compressed_path = filepath.with_suffix(filepath.suffix + '.zst')
                cmd = ['zstd', '-c', str(filepath)]
                with open(compressed_path, 'wb') as f_out:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=f_out,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                return compressed_path
            
            else:
                return filepath
                
        except Exception as e:
            logger.error(f"Erreur compression fichier {filepath}: {e}")
            raise
    
    async def _cleanup_loop(self):
        """Boucle de nettoyage des anciens backups"""
        while self.is_running:
            try:
                # Nettoyer les anciens backups
                await self._cleanup_old_backups()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(3600)  # Nettoyer toutes les heures
                
            except Exception as e:
                logger.error(f"Erreur nettoyage backups: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_old_backups(self):
        """Nettoie les anciens backups"""
        try:
            for config_name, config in self.configs.items():
                if not config.enabled:
                    continue
                
                # Récupérer les backups de cette configuration
                config_backups = [r for r in self.results.values() if r.config_name == config_name]
                
                # Trier par date de création
                config_backups.sort(key=lambda x: x.start_time, reverse=True)
                
                # Garder seulement les backups récents
                backups_to_keep = config.retention_days
                backups_to_delete = config_backups[backups_to_keep:]
                
                for backup in backups_to_delete:
                    if backup.file_path and os.path.exists(backup.file_path):
                        os.remove(backup.file_path)
                        logger.info(f"Backup supprimé: {backup.file_path}")
                    
                    # Supprimer du dictionnaire des résultats
                    if backup.backup_id in self.results:
                        del self.results[backup.backup_id]
                
        except Exception as e:
            logger.error(f"Erreur nettoyage anciens backups: {e}")
    
    async def _monitoring_loop(self):
        """Boucle de monitoring des backups"""
        while self.is_running:
            try:
                # Vérifier l'état des backups
                await self._monitor_backups()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(300)  # Vérifier toutes les 5 minutes
                
            except Exception as e:
                logger.error(f"Erreur monitoring backups: {e}")
                await asyncio.sleep(300)
    
    async def _monitor_backups(self):
        """Surveille l'état des backups"""
        try:
            # Vérifier les backups en cours
            in_progress = [r for r in self.results.values() if r.status == BackupStatus.IN_PROGRESS]
            
            for backup in in_progress:
                # Vérifier si le backup traîne
                if (datetime.utcnow() - backup.start_time).hours > 2:
                    logger.warning(f"Backup {backup.backup_id} en cours depuis plus de 2 heures")
            
            # Vérifier les backups échoués
            failed = [r for r in self.results.values() if r.status == BackupStatus.FAILED]
            
            if failed:
                logger.error(f"{len(failed)} backups ont échoué")
                
        except Exception as e:
            logger.error(f"Erreur monitoring backups: {e}")
    
    # Méthodes publiques
    
    async def create_backup_config(self, config: BackupConfig):
        """Crée une nouvelle configuration de backup"""
        self.configs[config.name] = config
        logger.info(f"Configuration de backup créée: {config.name}")
    
    async def update_backup_config(self, config_name: str, updates: Dict[str, Any]):
        """Met à jour une configuration de backup"""
        if config_name in self.configs:
            config = self.configs[config_name]
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            logger.info(f"Configuration de backup mise à jour: {config_name}")
    
    async def delete_backup_config(self, config_name: str):
        """Supprime une configuration de backup"""
        if config_name in self.configs:
            del self.configs[config_name]
            logger.info(f"Configuration de backup supprimée: {config_name}")
    
    async def execute_backup(self, config_name: str) -> str:
        """Exécute un backup manuellement"""
        if config_name not in self.configs:
            raise ValueError(f"Configuration de backup non trouvée: {config_name}")
        
        config = self.configs[config_name]
        await self._execute_backup(config)
        
        return f"Backup {config_name} exécuté"
    
    async def restore_backup(self, backup_id: str, target_database: str = None) -> bool:
        """Restaure un backup"""
        try:
            if backup_id not in self.results:
                raise ValueError(f"Backup non trouvé: {backup_id}")
            
            backup = self.results[backup_id]
            
            if backup.status != BackupStatus.COMPLETED:
                raise ValueError(f"Backup non terminé: {backup_id}")
            
            if not backup.file_path or not os.path.exists(backup.file_path):
                raise ValueError(f"Fichier de backup non trouvé: {backup.file_path}")
            
            # Décompresser si nécessaire
            if backup.file_path.endswith('.gz'):
                # Décompresser avec gzip
                decompressed_path = backup.file_path[:-3]
                with gzip.open(backup.file_path, 'rb') as f_in:
                    with open(decompressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = decompressed_path
            else:
                restore_file = backup.file_path
            
            # Exécuter la restauration
            target_db = target_database or "cryptospreadedge"
            
            cmd = [
                "psql",
                "-h", "localhost",
                "-U", "trading_user",
                "-d", target_db,
                "-f", restore_file
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erreur restauration: {stderr.decode()}")
            
            # Nettoyer le fichier décompressé temporaire
            if restore_file != backup.file_path:
                os.remove(restore_file)
            
            logger.info(f"Backup {backup_id} restauré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur restauration backup {backup_id}: {e}")
            return False
    
    async def get_backup_status(self) -> Dict[str, Any]:
        """Récupère le statut des backups"""
        try:
            total_backups = len(self.results)
            completed_backups = len([r for r in self.results.values() if r.status == BackupStatus.COMPLETED])
            failed_backups = len([r for r in self.results.values() if r.status == BackupStatus.FAILED])
            in_progress_backups = len([r for r in self.results.values() if r.status == BackupStatus.IN_PROGRESS])
            
            return {
                "total_backups": total_backups,
                "completed_backups": completed_backups,
                "failed_backups": failed_backups,
                "in_progress_backups": in_progress_backups,
                "success_rate": completed_backups / total_backups if total_backups > 0 else 0,
                "configurations": len(self.configs),
                "enabled_configurations": len([c for c in self.configs.values() if c.enabled])
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération statut backups: {e}")
            return {}
    
    async def get_backup_list(self, config_name: str = None) -> List[BackupResult]:
        """Récupère la liste des backups"""
        try:
            if config_name:
                return [r for r in self.results.values() if r.config_name == config_name]
            else:
                return list(self.results.values())
                
        except Exception as e:
            logger.error(f"Erreur récupération liste backups: {e}")
            return []
    
    async def get_backup_info(self, backup_id: str) -> Optional[BackupResult]:
        """Récupère les informations d'un backup"""
        return self.results.get(backup_id)