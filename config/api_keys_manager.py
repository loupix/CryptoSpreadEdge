"""
Gestionnaire des clés API pour toutes les plateformes
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class APIKey:
    """Clé API d'une plateforme"""
    platform: str
    api_key: str
    secret_key: str = ""
    passphrase: str = ""
    extra_params: Dict[str, str] = None
    enabled: bool = True
    created_at: str = ""
    last_used: str = ""
    usage_count: int = 0
    rate_limit: int = 0
    expires_at: str = ""


class APIKeysManager:
    """Gestionnaire des clés API"""
    
    def __init__(self, config_dir: str = "config/environments"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.keys_file = self.config_dir / "api_keys.json"
        self.encrypted_file = self.config_dir / "api_keys.encrypted"
        
        # Clé de chiffrement (à générer ou récupérer)
        self.encryption_key = self._get_or_create_encryption_key()
        
        # Charger les clés existantes
        self.api_keys: Dict[str, APIKey] = {}
        self._load_keys()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Récupère ou crée une clé de chiffrement"""
        key_file = self.config_dir / "encryption.key"
        
        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Générer une nouvelle clé
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key
    
    def _encrypt_data(self, data: str) -> str:
        """Chiffre les données"""
        f = Fernet(self.encryption_key)
        encrypted_data = f.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Déchiffre les données"""
        f = Fernet(self.encryption_key)
        decoded_data = base64.b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded_data)
        return decrypted_data.decode()
    
    def _load_keys(self):
        """Charge les clés API depuis le fichier"""
        try:
            if self.encrypted_file.exists():
                # Charger depuis le fichier chiffré
                with open(self.encrypted_file, "r") as f:
                    encrypted_data = f.read()
                
                decrypted_data = self._decrypt_data(encrypted_data)
                keys_data = json.loads(decrypted_data)
                
                for platform, key_data in keys_data.items():
                    self.api_keys[platform] = APIKey(**key_data)
                
                self.logger.info(f"Chargé {len(self.api_keys)} clés API")
            elif self.keys_file.exists():
                # Charger depuis le fichier non chiffré (migration)
                with open(self.keys_file, "r") as f:
                    keys_data = json.load(f)
                
                for platform, key_data in keys_data.items():
                    self.api_keys[platform] = APIKey(**key_data)
                
                # Migrer vers le format chiffré
                self._save_keys()
                self.logger.info(f"Migré {len(self.api_keys)} clés API vers le format chiffré")
            else:
                self.logger.info("Aucune clé API trouvée")
        
        except Exception as e:
            self.logger.error(f"Erreur chargement clés API: {e}")
    
    def _save_keys(self):
        """Sauvegarde les clés API"""
        try:
            # Préparer les données
            keys_data = {}
            for platform, api_key in self.api_keys.items():
                keys_data[platform] = asdict(api_key)
            
            # Chiffrer et sauvegarder
            json_data = json.dumps(keys_data, indent=2)
            encrypted_data = self._encrypt_data(json_data)
            
            with open(self.encrypted_file, "w") as f:
                f.write(encrypted_data)
            
            # Supprimer l'ancien fichier non chiffré
            if self.keys_file.exists():
                self.keys_file.unlink()
            
            self.logger.info(f"Sauvegardé {len(self.api_keys)} clés API")
        
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde clés API: {e}")
    
    def add_api_key(
        self, 
        platform: str, 
        api_key: str, 
        secret_key: str = "", 
        passphrase: str = "",
        extra_params: Dict[str, str] = None,
        enabled: bool = True
    ) -> bool:
        """Ajoute une clé API"""
        try:
            from datetime import datetime
            
            api_key_obj = APIKey(
                platform=platform,
                api_key=api_key,
                secret_key=secret_key,
                passphrase=passphrase,
                extra_params=extra_params or {},
                enabled=enabled,
                created_at=datetime.utcnow().isoformat(),
                last_used="",
                usage_count=0,
                rate_limit=0
            )
            
            self.api_keys[platform] = api_key_obj
            self._save_keys()
            
            self.logger.info(f"Clé API ajoutée pour {platform}")
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur ajout clé API {platform}: {e}")
            return False
    
    def update_api_key(self, platform: str, **kwargs) -> bool:
        """Met à jour une clé API"""
        try:
            if platform not in self.api_keys:
                self.logger.error(f"Clé API non trouvée pour {platform}")
                return False
            
            # Mettre à jour les champs fournis
            for key, value in kwargs.items():
                if hasattr(self.api_keys[platform], key):
                    setattr(self.api_keys[platform], key, value)
            
            self._save_keys()
            self.logger.info(f"Clé API mise à jour pour {platform}")
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour clé API {platform}: {e}")
            return False
    
    def remove_api_key(self, platform: str) -> bool:
        """Supprime une clé API"""
        try:
            if platform not in self.api_keys:
                self.logger.error(f"Clé API non trouvée pour {platform}")
                return False
            
            del self.api_keys[platform]
            self._save_keys()
            
            self.logger.info(f"Clé API supprimée pour {platform}")
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur suppression clé API {platform}: {e}")
            return False
    
    def get_api_key(self, platform: str) -> Optional[APIKey]:
        """Récupère une clé API"""
        return self.api_keys.get(platform)
    
    def get_all_api_keys(self) -> Dict[str, APIKey]:
        """Récupère toutes les clés API"""
        return self.api_keys.copy()
    
    def get_enabled_api_keys(self) -> Dict[str, APIKey]:
        """Récupère les clés API activées"""
        return {
            platform: api_key for platform, api_key in self.api_keys.items()
            if api_key.enabled
        }
    
    def get_platforms_with_keys(self) -> List[str]:
        """Récupère la liste des plateformes avec des clés"""
        return list(self.api_keys.keys())
    
    def get_platforms_without_keys(self) -> List[str]:
        """Récupère la liste des plateformes sans clés"""
        from .platforms_config import ALL_PLATFORM_CONFIGS
        
        platforms_with_keys = set(self.api_keys.keys())
        all_platforms = set(ALL_PLATFORM_CONFIGS.keys())
        
        return list(all_platforms - platforms_with_keys)
    
    def get_credentials_for_platform(self, platform: str) -> Dict[str, str]:
        """Récupère les identifiants pour une plateforme"""
        api_key = self.get_api_key(platform)
        if not api_key or not api_key.enabled:
            return {}
        
        credentials = {
            "api_key": api_key.api_key,
            "secret_key": api_key.secret_key
        }
        
        if api_key.passphrase:
            credentials["passphrase"] = api_key.passphrase
        
        if api_key.extra_params:
            credentials.update(api_key.extra_params)
        
        return credentials
    
    def get_all_credentials(self) -> Dict[str, Dict[str, str]]:
        """Récupère tous les identifiants"""
        credentials = {}
        
        for platform, api_key in self.get_enabled_api_keys().items():
            credentials[platform] = self.get_credentials_for_platform(platform)
        
        return credentials
    
    def update_usage(self, platform: str):
        """Met à jour l'utilisation d'une clé API"""
        try:
            if platform in self.api_keys:
                from datetime import datetime
                
                self.api_keys[platform].last_used = datetime.utcnow().isoformat()
                self.api_keys[platform].usage_count += 1
                
                # Sauvegarder périodiquement
                if self.api_keys[platform].usage_count % 10 == 0:
                    self._save_keys()
        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour utilisation {platform}: {e}")
    
    def enable_platform(self, platform: str) -> bool:
        """Active une plateforme"""
        return self.update_api_key(platform, enabled=True)
    
    def disable_platform(self, platform: str) -> bool:
        """Désactive une plateforme"""
        return self.update_api_key(platform, enabled=False)
    
    def get_platform_status(self) -> Dict[str, Dict[str, Any]]:
        """Retourne le statut des plateformes"""
        status = {}
        
        for platform, api_key in self.api_keys.items():
            status[platform] = {
                "has_key": True,
                "enabled": api_key.enabled,
                "has_secret": bool(api_key.secret_key),
                "has_passphrase": bool(api_key.passphrase),
                "usage_count": api_key.usage_count,
                "last_used": api_key.last_used,
                "created_at": api_key.created_at
            }
        
        # Ajouter les plateformes sans clés
        for platform in self.get_platforms_without_keys():
            status[platform] = {
                "has_key": False,
                "enabled": False,
                "has_secret": False,
                "has_passphrase": False,
                "usage_count": 0,
                "last_used": "",
                "created_at": ""
            }
        
        return status
    
    def validate_api_key(self, platform: str) -> bool:
        """Valide une clé API"""
        try:
            api_key = self.get_api_key(platform)
            if not api_key or not api_key.enabled:
                return False
            
            # Vérifications de base
            if not api_key.api_key:
                return False
            
            # Vérifier la longueur minimale
            if len(api_key.api_key) < 10:
                return False
            
            # Vérifier le format (basique)
            if platform in ["binance", "okx", "bybit"]:
                # Ces plateformes ont des clés API spécifiques
                if not api_key.secret_key:
                    return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur validation clé API {platform}: {e}")
            return False
    
    def get_platforms_needing_keys(self) -> List[str]:
        """Récupère les plateformes nécessitant des clés API"""
        from .platforms_config import ALL_PLATFORM_CONFIGS
        
        platforms_needing_keys = []
        
        for platform, config in ALL_PLATFORM_CONFIGS.items():
            if config.api_required and platform not in self.api_keys:
                platforms_needing_keys.append(platform)
        
        return platforms_needing_keys
    
    def get_platforms_ready_for_trading(self) -> List[str]:
        """Récupère les plateformes prêtes pour le trading"""
        from .platforms_config import ALL_PLATFORM_CONFIGS
        
        ready_platforms = []
        
        for platform, config in ALL_PLATFORM_CONFIGS.items():
            if (config.enabled and 
                config.platform_type.value in ["exchange", "dex"] and
                self.validate_api_key(platform)):
                ready_platforms.append(platform)
        
        return ready_platforms
    
    def get_platforms_ready_for_data(self) -> List[str]:
        """Récupère les plateformes prêtes pour les données"""
        from .platforms_config import ALL_PLATFORM_CONFIGS
        
        ready_platforms = []
        
        for platform, config in ALL_PLATFORM_CONFIGS.items():
            if (config.enabled and 
                config.platform_type.value in ["data_source", "aggregator"] and
                (not config.api_required or self.validate_api_key(platform))):
                ready_platforms.append(platform)
        
        return ready_platforms
    
    def export_keys(self, file_path: str, include_secrets: bool = False) -> bool:
        """Exporte les clés API vers un fichier"""
        try:
            export_data = {}
            
            for platform, api_key in self.api_keys.items():
                if include_secrets:
                    export_data[platform] = asdict(api_key)
                else:
                    # Exporter sans les secrets
                    safe_data = asdict(api_key)
                    safe_data["api_key"] = "***" if api_key.api_key else ""
                    safe_data["secret_key"] = "***" if api_key.secret_key else ""
                    safe_data["passphrase"] = "***" if api_key.passphrase else ""
                    export_data[platform] = safe_data
            
            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Clés API exportées vers {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur export clés API: {e}")
            return False
    
    def import_keys(self, file_path: str) -> bool:
        """Importe les clés API depuis un fichier"""
        try:
            with open(file_path, "r") as f:
                import_data = json.load(f)
            
            imported_count = 0
            
            for platform, key_data in import_data.items():
                if self.add_api_key(
                    platform=platform,
                    api_key=key_data.get("api_key", ""),
                    secret_key=key_data.get("secret_key", ""),
                    passphrase=key_data.get("passphrase", ""),
                    extra_params=key_data.get("extra_params", {}),
                    enabled=key_data.get("enabled", True)
                ):
                    imported_count += 1
            
            self.logger.info(f"Importé {imported_count} clés API depuis {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur import clés API: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des clés API"""
        total_platforms = len(self.api_keys)
        enabled_platforms = len(self.get_enabled_api_keys())
        platforms_with_secrets = len([k for k in self.api_keys.values() if k.secret_key])
        platforms_with_passphrase = len([k for k in self.api_keys.values() if k.passphrase])
        
        return {
            "total_platforms": total_platforms,
            "enabled_platforms": enabled_platforms,
            "platforms_with_secrets": platforms_with_secrets,
            "platforms_with_passphrase": platforms_with_passphrase,
            "platforms_ready_for_trading": len(self.get_platforms_ready_for_trading()),
            "platforms_ready_for_data": len(self.get_platforms_ready_for_data()),
            "platforms_needing_keys": len(self.get_platforms_needing_keys())
        }


# Instance globale du gestionnaire de clés API
api_keys_manager = APIKeysManager()