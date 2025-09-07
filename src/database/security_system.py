"""
Système de sécurité et d'audit avancé pour CryptoSpreadEdge
"""

import asyncio
import logging
import hashlib
import hmac
import secrets
import base64
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from .extended_models import User, ExchangeAPIKey, AuditLog
from .extended_repositories import UserRepository, ExchangeAPIKeyRepository

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Niveaux de sécurité"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditAction(Enum):
    """Actions d'audit"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    API_KEY_CREATE = "api_key_create"
    API_KEY_DELETE = "api_key_delete"
    API_KEY_UPDATE = "api_key_update"
    PERMISSION_CHANGE = "permission_change"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    SYSTEM_CONFIG = "system_config"
    SECURITY_VIOLATION = "security_violation"


class EncryptionType(Enum):
    """Types de chiffrement"""
    AES256 = "aes256"
    FERNET = "fernet"
    RSA = "rsa"
    PBKDF2 = "pbkdf2"


@dataclass
class SecurityPolicy:
    """Politique de sécurité"""
    name: str
    description: str
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    session_timeout: int = 3600  # 1 heure
    require_2fa: bool = False
    password_history: int = 5
    api_key_rotation: int = 90  # jours
    encryption_required: bool = True
    audit_level: SecurityLevel = SecurityLevel.MEDIUM


@dataclass
class SecurityEvent:
    """Événement de sécurité"""
    event_id: str
    user_id: Optional[str]
    action: AuditAction
    severity: SecurityLevel
    description: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False


class SecuritySystem:
    """Système de sécurité et d'audit"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.user_repo = UserRepository(db_session)
        self.api_key_repo = ExchangeAPIKeyRepository(db_session)
        
        # Configuration de sécurité
        self.security_policy = SecurityPolicy(
            name="default",
            description="Politique de sécurité par défaut"
        )
        
        # Clés de chiffrement
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Cache de sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.failed_login_attempts: Dict[str, List[datetime]] = {}
        
        # Événements de sécurité
        self.security_events: List[SecurityEvent] = []
        
        # Configuration
        self.is_running = False
        self.audit_retention_days = 365
        self.encryption_algorithm = EncryptionType.FERNET
    
    def _generate_encryption_key(self) -> bytes:
        """Génère une clé de chiffrement"""
        return Fernet.generate_key()
    
    def _generate_salt(self) -> bytes:
        """Génère un sel pour le hachage"""
        return secrets.token_bytes(32)
    
    def _hash_password(self, password: str, salt: bytes = None) -> Tuple[str, bytes]:
        """Hache un mot de passe"""
        if salt is None:
            salt = self._generate_salt()
        
        # Utiliser PBKDF2 avec SHA-256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt
    
    def _verify_password(self, password: str, hashed_password: str, salt: bytes) -> bool:
        """Vérifie un mot de passe"""
        try:
            key, _ = self._hash_password(password, salt)
            return hmac.compare_digest(key, hashed_password)
        except Exception:
            return False
    
    def _encrypt_data(self, data: str) -> str:
        """Chiffre des données"""
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Erreur chiffrement données: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Déchiffre des données"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Erreur déchiffrement données: {e}")
            raise
    
    def _validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Valide un mot de passe selon la politique"""
        errors = []
        
        if len(password) < self.security_policy.min_password_length:
            errors.append(f"Le mot de passe doit contenir au moins {self.security_policy.min_password_length} caractères")
        
        if self.security_policy.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Le mot de passe doit contenir au moins une majuscule")
        
        if self.security_policy.require_lowercase and not any(c.islower() for c in password):
            errors.append("Le mot de passe doit contenir au moins une minuscule")
        
        if self.security_policy.require_numbers and not any(c.isdigit() for c in password):
            errors.append("Le mot de passe doit contenir au moins un chiffre")
        
        if self.security_policy.require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial")
        
        return len(errors) == 0, errors
    
    def _generate_2fa_secret(self) -> str:
        """Génère un secret 2FA"""
        return base64.b32encode(secrets.token_bytes(20)).decode()
    
    def _verify_2fa_token(self, secret: str, token: str) -> bool:
        """Vérifie un token 2FA"""
        try:
            import pyotp
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)
        except Exception as e:
            logger.error(f"Erreur vérification 2FA: {e}")
            return False
    
    async def start(self):
        """Démarre le système de sécurité"""
        self.is_running = True
        logger.info("Système de sécurité démarré")
        
        # Démarrer les tâches de sécurité
        asyncio.create_task(self._security_monitoring_loop())
        asyncio.create_task(self._cleanup_loop())
        asyncio.create_task(self._audit_loop())
    
    async def stop(self):
        """Arrête le système de sécurité"""
        self.is_running = False
        logger.info("Système de sécurité arrêté")
    
    async def _security_monitoring_loop(self):
        """Boucle de monitoring de sécurité"""
        while self.is_running:
            try:
                # Vérifier les tentatives de connexion échouées
                await self._check_failed_logins()
                
                # Vérifier les sessions expirées
                await self._check_expired_sessions()
                
                # Vérifier les clés API expirées
                await self._check_expired_api_keys()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(60)  # Vérifier toutes les minutes
                
            except Exception as e:
                logger.error(f"Erreur monitoring sécurité: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self):
        """Boucle de nettoyage"""
        while self.is_running:
            try:
                # Nettoyer les anciens événements de sécurité
                await self._cleanup_old_security_events()
                
                # Nettoyer les tentatives de connexion échouées
                await self._cleanup_failed_logins()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(3600)  # Nettoyer toutes les heures
                
            except Exception as e:
                logger.error(f"Erreur nettoyage sécurité: {e}")
                await asyncio.sleep(3600)
    
    async def _audit_loop(self):
        """Boucle d'audit"""
        while self.is_running:
            try:
                # Traiter les événements d'audit en attente
                await self._process_audit_events()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(30)  # Traiter toutes les 30 secondes
                
            except Exception as e:
                logger.error(f"Erreur audit: {e}")
                await asyncio.sleep(30)
    
    async def _check_failed_logins(self):
        """Vérifie les tentatives de connexion échouées"""
        try:
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(seconds=self.security_policy.lockout_duration)
            
            # Nettoyer les tentatives anciennes
            for user_id in list(self.failed_login_attempts.keys()):
                self.failed_login_attempts[user_id] = [
                    attempt for attempt in self.failed_login_attempts[user_id]
                    if attempt > cutoff_time
                ]
                
                if not self.failed_login_attempts[user_id]:
                    del self.failed_login_attempts[user_id]
            
            # Vérifier les comptes verrouillés
            for user_id, attempts in self.failed_login_attempts.items():
                if len(attempts) >= self.security_policy.max_login_attempts:
                    # Déverrouiller le compte si le délai est écoulé
                    if attempts[-1] < cutoff_time:
                        del self.failed_login_attempts[user_id]
                        await self._unlock_user_account(user_id)
                    else:
                        # Maintenir le verrouillage
                        await self._lock_user_account(user_id)
                        
        except Exception as e:
            logger.error(f"Erreur vérification connexions échouées: {e}")
    
    async def _check_expired_sessions(self):
        """Vérifie les sessions expirées"""
        try:
            current_time = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session_data in self.active_sessions.items():
                if current_time - session_data['created_at'] > timedelta(seconds=self.security_policy.session_timeout):
                    expired_sessions.append(session_id)
            
            # Supprimer les sessions expirées
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Session expirée supprimée: {session_id}")
                
        except Exception as e:
            logger.error(f"Erreur vérification sessions expirées: {e}")
    
    async def _check_expired_api_keys(self):
        """Vérifie les clés API expirées"""
        try:
            # Récupérer les clés API expirées
            expired_keys = await self.api_key_repo.get_expired_keys()
            
            for key in expired_keys:
                # Désactiver la clé
                await self.api_key_repo.deactivate_key(str(key.id))
                
                # Enregistrer l'événement
                await self._log_security_event(
                    user_id=str(key.user_id),
                    action=AuditAction.API_KEY_DELETE,
                    severity=SecurityLevel.MEDIUM,
                    description=f"Clé API expirée désactivée: {key.name}",
                    metadata={"key_id": str(key.id), "expired_at": key.expires_at.isoformat()}
                )
                
        except Exception as e:
            logger.error(f"Erreur vérification clés API expirées: {e}")
    
    async def _cleanup_old_security_events(self):
        """Nettoie les anciens événements de sécurité"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=self.audit_retention_days)
            
            # Supprimer les événements anciens
            self.security_events = [
                event for event in self.security_events
                if event.timestamp > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Erreur nettoyage événements sécurité: {e}")
    
    async def _cleanup_failed_logins(self):
        """Nettoie les tentatives de connexion échouées"""
        try:
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(hours=24)
            
            # Nettoyer les tentatives anciennes
            for user_id in list(self.failed_login_attempts.keys()):
                self.failed_login_attempts[user_id] = [
                    attempt for attempt in self.failed_login_attempts[user_id]
                    if attempt > cutoff_time
                ]
                
                if not self.failed_login_attempts[user_id]:
                    del self.failed_login_attempts[user_id]
                    
        except Exception as e:
            logger.error(f"Erreur nettoyage connexions échouées: {e}")
    
    async def _process_audit_events(self):
        """Traite les événements d'audit"""
        try:
            # Traiter les événements de sécurité non résolus
            unresolved_events = [
                event for event in self.security_events
                if not event.resolved and event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
            ]
            
            for event in unresolved_events:
                await self._handle_security_event(event)
                
        except Exception as e:
            logger.error(f"Erreur traitement événements audit: {e}")
    
    async def _handle_security_event(self, event: SecurityEvent):
        """Traite un événement de sécurité"""
        try:
            if event.severity == SecurityLevel.CRITICAL:
                # Événement critique - action immédiate
                await self._handle_critical_security_event(event)
            elif event.severity == SecurityLevel.HIGH:
                # Événement de haute priorité
                await self._handle_high_priority_security_event(event)
            
            # Marquer comme résolu
            event.resolved = True
            
        except Exception as e:
            logger.error(f"Erreur traitement événement sécurité {event.event_id}: {e}")
    
    async def _handle_critical_security_event(self, event: SecurityEvent):
        """Traite un événement de sécurité critique"""
        try:
            # Verrouiller le compte utilisateur
            if event.user_id:
                await self._lock_user_account(event.user_id)
            
            # Envoyer une alerte
            await self._send_security_alert(event)
            
            logger.critical(f"Événement de sécurité critique traité: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Erreur traitement événement critique {event.event_id}: {e}")
    
    async def _handle_high_priority_security_event(self, event: SecurityEvent):
        """Traite un événement de sécurité de haute priorité"""
        try:
            # Envoyer une notification
            await self._send_security_notification(event)
            
            logger.warning(f"Événement de sécurité haute priorité traité: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Erreur traitement événement haute priorité {event.event_id}: {e}")
    
    async def _lock_user_account(self, user_id: str):
        """Verrouille un compte utilisateur"""
        try:
            await self.user_repo.lock_account(user_id)
            logger.info(f"Compte utilisateur verrouillé: {user_id}")
            
        except Exception as e:
            logger.error(f"Erreur verrouillage compte {user_id}: {e}")
    
    async def _unlock_user_account(self, user_id: str):
        """Déverrouille un compte utilisateur"""
        try:
            await self.user_repo.unlock_account(user_id)
            logger.info(f"Compte utilisateur déverrouillé: {user_id}")
            
        except Exception as e:
            logger.error(f"Erreur déverrouillage compte {user_id}: {e}")
    
    async def _send_security_alert(self, event: SecurityEvent):
        """Envoie une alerte de sécurité"""
        try:
            # Implémentation de l'envoi d'alerte
            logger.critical(f"ALERTE SÉCURITÉ: {event.description}")
            
        except Exception as e:
            logger.error(f"Erreur envoi alerte sécurité: {e}")
    
    async def _send_security_notification(self, event: SecurityEvent):
        """Envoie une notification de sécurité"""
        try:
            # Implémentation de l'envoi de notification
            logger.warning(f"NOTIFICATION SÉCURITÉ: {event.description}")
            
        except Exception as e:
            logger.error(f"Erreur envoi notification sécurité: {e}")
    
    # Méthodes publiques
    
    async def authenticate_user(self, username: str, password: str, 
                              ip_address: str, user_agent: str) -> Tuple[bool, Optional[str], str]:
        """Authentifie un utilisateur"""
        try:
            # Récupérer l'utilisateur
            user = await self.user_repo.get_by_username(username)
            
            if not user:
                await self._log_security_event(
                    user_id=None,
                    action=AuditAction.LOGIN_FAILED,
                    severity=SecurityLevel.MEDIUM,
                    description=f"Tentative de connexion avec nom d'utilisateur inexistant: {username}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return False, None, "Nom d'utilisateur ou mot de passe incorrect"
            
            # Vérifier si le compte est verrouillé
            if user.locked_until and user.locked_until > datetime.utcnow():
                await self._log_security_event(
                    user_id=str(user.id),
                    action=AuditAction.LOGIN_FAILED,
                    severity=SecurityLevel.HIGH,
                    description=f"Tentative de connexion sur compte verrouillé: {username}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return False, None, "Compte temporairement verrouillé"
            
            # Vérifier le mot de passe
            if not self._verify_password(password, user.password_hash, user.password_salt):
                # Enregistrer la tentative échouée
                if str(user.id) not in self.failed_login_attempts:
                    self.failed_login_attempts[str(user.id)] = []
                
                self.failed_login_attempts[str(user.id)].append(datetime.utcnow())
                
                await self._log_security_event(
                    user_id=str(user.id),
                    action=AuditAction.LOGIN_FAILED,
                    severity=SecurityLevel.MEDIUM,
                    description=f"Tentative de connexion avec mot de passe incorrect: {username}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return False, None, "Nom d'utilisateur ou mot de passe incorrect"
            
            # Connexion réussie
            await self.user_repo.update_last_login(str(user.id))
            
            # Créer une session
            session_id = str(uuid.uuid4())
            self.active_sessions[session_id] = {
                'user_id': str(user.id),
                'username': username,
                'created_at': datetime.utcnow(),
                'ip_address': ip_address,
                'user_agent': user_agent
            }
            
            # Nettoyer les tentatives échouées
            if str(user.id) in self.failed_login_attempts:
                del self.failed_login_attempts[str(user.id)]
            
            await self._log_security_event(
                user_id=str(user.id),
                action=AuditAction.LOGIN,
                severity=SecurityLevel.LOW,
                description=f"Connexion réussie: {username}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return True, session_id, "Connexion réussie"
            
        except Exception as e:
            logger.error(f"Erreur authentification utilisateur: {e}")
            return False, None, "Erreur d'authentification"
    
    async def change_password(self, user_id: str, old_password: str, 
                            new_password: str, ip_address: str) -> Tuple[bool, str]:
        """Change le mot de passe d'un utilisateur"""
        try:
            # Récupérer l'utilisateur
            user = await self.user_repo.get_by_id(user_id)
            
            if not user:
                return False, "Utilisateur non trouvé"
            
            # Vérifier l'ancien mot de passe
            if not self._verify_password(old_password, user.password_hash, user.password_salt):
                await self._log_security_event(
                    user_id=user_id,
                    action=AuditAction.PASSWORD_CHANGE,
                    severity=SecurityLevel.MEDIUM,
                    description="Tentative de changement de mot de passe avec ancien mot de passe incorrect",
                    ip_address=ip_address,
                    user_agent=""
                )
                return False, "Ancien mot de passe incorrect"
            
            # Valider le nouveau mot de passe
            is_valid, errors = self._validate_password(new_password)
            if not is_valid:
                return False, f"Mot de passe invalide: {', '.join(errors)}"
            
            # Hacher le nouveau mot de passe
            new_salt = self._generate_salt()
            new_hash, _ = self._hash_password(new_password, new_salt)
            
            # Mettre à jour en base
            await self.user_repo.update_password(user_id, new_hash, new_salt)
            
            await self._log_security_event(
                user_id=user_id,
                action=AuditAction.PASSWORD_CHANGE,
                severity=SecurityLevel.LOW,
                description="Mot de passe changé avec succès",
                ip_address=ip_address,
                user_agent=""
            )
            
            return True, "Mot de passe changé avec succès"
            
        except Exception as e:
            logger.error(f"Erreur changement mot de passe: {e}")
            return False, "Erreur lors du changement de mot de passe"
    
    async def create_api_key(self, user_id: str, exchange_id: str, 
                           api_key: str, secret_key: str, 
                           passphrase: str = None, ip_address: str = "") -> Tuple[bool, str]:
        """Crée une clé API chiffrée"""
        try:
            # Chiffrer les clés
            encrypted_api_key = self._encrypt_data(api_key)
            encrypted_secret_key = self._encrypt_data(secret_key)
            encrypted_passphrase = self._encrypt_data(passphrase) if passphrase else None
            
            # Créer la clé API
            api_key_data = {
                "user_id": user_id,
                "exchange_id": exchange_id,
                "name": f"API Key {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                "api_key": encrypted_api_key,
                "secret_key": encrypted_secret_key,
                "passphrase": encrypted_passphrase,
                "is_active": True,
                "permissions": ["read", "trade"],
                "expires_at": datetime.utcnow() + timedelta(days=self.security_policy.api_key_rotation)
            }
            
            await self.api_key_repo.create(api_key_data)
            
            await self._log_security_event(
                user_id=user_id,
                action=AuditAction.API_KEY_CREATE,
                severity=SecurityLevel.MEDIUM,
                description=f"Clé API créée pour l'exchange {exchange_id}",
                ip_address=ip_address,
                user_agent=""
            )
            
            return True, "Clé API créée avec succès"
            
        except Exception as e:
            logger.error(f"Erreur création clé API: {e}")
            return False, "Erreur lors de la création de la clé API"
    
    async def get_decrypted_api_key(self, api_key_id: str, user_id: str) -> Optional[Dict[str, str]]:
        """Récupère une clé API déchiffrée"""
        try:
            # Récupérer la clé API
            api_key = await self.api_key_repo.get_by_id(api_key_id)
            
            if not api_key or str(api_key.user_id) != user_id:
                return None
            
            # Déchiffrer les clés
            decrypted_data = {
                "api_key": self._decrypt_data(api_key.api_key),
                "secret_key": self._decrypt_data(api_key.secret_key)
            }
            
            if api_key.passphrase:
                decrypted_data["passphrase"] = self._decrypt_data(api_key.passphrase)
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Erreur récupération clé API déchiffrée: {e}")
            return None
    
    async def _log_security_event(self, user_id: Optional[str], action: AuditAction,
                                severity: SecurityLevel, description: str,
                                ip_address: str = "", user_agent: str = "",
                                metadata: Dict[str, Any] = None):
        """Enregistre un événement de sécurité"""
        try:
            event = SecurityEvent(
                event_id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                severity=severity,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            self.security_events.append(event)
            
            # Enregistrer en base de données
            audit_data = {
                "entity_type": "security_event",
                "entity_id": event.event_id,
                "action": action.value,
                "old_values": None,
                "new_values": {
                    "severity": severity.value,
                    "description": description,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                },
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "metadata": metadata or {}
            }
            
            from .repositories import BaseRepository
            base_repo = BaseRepository(self.db_session)
            await base_repo._log_audit(**audit_data)
            
        except Exception as e:
            logger.error(f"Erreur enregistrement événement sécurité: {e}")
    
    async def get_security_events(self, user_id: str = None, 
                                severity: SecurityLevel = None,
                                limit: int = 100) -> List[SecurityEvent]:
        """Récupère les événements de sécurité"""
        try:
            events = self.security_events.copy()
            
            if user_id:
                events = [e for e in events if e.user_id == user_id]
            
            if severity:
                events = [e for e in events if e.severity == severity]
            
            # Trier par timestamp décroissant
            events.sort(key=lambda x: x.timestamp, reverse=True)
            
            return events[:limit]
            
        except Exception as e:
            logger.error(f"Erreur récupération événements sécurité: {e}")
            return []
    
    async def get_security_summary(self) -> Dict[str, Any]:
        """Récupère un résumé de sécurité"""
        try:
            current_time = datetime.utcnow()
            last_24h = current_time - timedelta(hours=24)
            
            # Compter les événements par sévérité
            events_by_severity = defaultdict(int)
            for event in self.security_events:
                if event.timestamp >= last_24h:
                    events_by_severity[event.severity.value] += 1
            
            # Compter les tentatives de connexion échouées
            total_failed_logins = sum(len(attempts) for attempts in self.failed_login_attempts.values())
            
            # Compter les sessions actives
            active_sessions = len(self.active_sessions)
            
            return {
                "timestamp": current_time,
                "events_last_24h": events_by_severity,
                "failed_logins": total_failed_logins,
                "active_sessions": active_sessions,
                "locked_accounts": len(self.failed_login_attempts),
                "security_level": self.security_policy.audit_level.value
            }
            
        except Exception as e:
            logger.error(f"Erreur résumé sécurité: {e}")
            return {}
    
    async def update_security_policy(self, policy_updates: Dict[str, Any]):
        """Met à jour la politique de sécurité"""
        try:
            for key, value in policy_updates.items():
                if hasattr(self.security_policy, key):
                    setattr(self.security_policy, key, value)
            
            logger.info("Politique de sécurité mise à jour")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour politique sécurité: {e}")
    
    async def validate_session(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """Valide une session"""
        try:
            if session_id not in self.active_sessions:
                return False, None
            
            session_data = self.active_sessions[session_id]
            
            # Vérifier si la session est expirée
            if (datetime.utcnow() - session_data['created_at'] > 
                timedelta(seconds=self.security_policy.session_timeout)):
                del self.active_sessions[session_id]
                return False, None
            
            return True, session_data['user_id']
            
        except Exception as e:
            logger.error(f"Erreur validation session: {e}")
            return False, None
    
    async def logout_user(self, session_id: str, ip_address: str = ""):
        """Déconnecte un utilisateur"""
        try:
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]
                
                await self._log_security_event(
                    user_id=session_data['user_id'],
                    action=AuditAction.LOGOUT,
                    severity=SecurityLevel.LOW,
                    description="Déconnexion utilisateur",
                    ip_address=ip_address,
                    user_agent=""
                )
                
                del self.active_sessions[session_id]
                
        except Exception as e:
            logger.error(f"Erreur déconnexion utilisateur: {e}")