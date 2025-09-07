# Gestionnaire d'authentification pour l'API mobile
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt

class AuthManager:
    """Gestionnaire d'authentification pour l'API mobile"""
    
    def __init__(self):
        self.secret_key = "cryptospreadedge_secret_key_2024"  # À changer en production
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 30
        
        # Base de données simulée (à remplacer par une vraie DB)
        self.users_db = {}
        self.refresh_tokens_db = {}
    
    def hash_password(self, password: str) -> str:
        """Hasher un mot de passe"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Vérifier un mot de passe"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def create_access_token(self, user_id: str) -> str:
        """Créer un token d'accès"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Créer un token de rafraîchissement"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        token = secrets.token_urlsafe(32)
        
        # Stocker le token de rafraîchissement
        self.refresh_tokens_db[token] = {
            "user_id": user_id,
            "expires": expire
        }
        
        return token
    
    def verify_access_token(self, token: str) -> Optional[str]:
        """Vérifier un token d'accès et retourner l'ID utilisateur"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "access":
                return None
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[str]:
        """Vérifier un token de rafraîchissement et retourner l'ID utilisateur"""
        if token not in self.refresh_tokens_db:
            return None
        
        token_data = self.refresh_tokens_db[token]
        if datetime.utcnow() > token_data["expires"]:
            del self.refresh_tokens_db[token]
            return None
        
        return token_data["user_id"]
    
    async def create_user(self, email: str, password: str, username: str) -> Dict[str, Any]:
        """Créer un nouvel utilisateur"""
        user_id = secrets.token_hex(16)
        hashed_password = self.hash_password(password)
        
        user = {
            "id": user_id,
            "email": email,
            "username": username,
            "password": hashed_password,
            "isAuthenticated": True,
            "preferences": {
                "theme": "light",
                "currency": "USD",
                "language": "fr",
                "notifications": {
                    "priceAlerts": True,
                    "tradeAlerts": True,
                    "systemAlerts": True,
                    "pushEnabled": True
                }
            },
            "createdAt": datetime.utcnow().isoformat()
        }
        
        self.users_db[user_id] = user
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Récupérer un utilisateur par email"""
        for user in self.users_db.values():
            if user["email"] == email:
                return user
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un utilisateur par ID"""
        return self.users_db.get(user_id)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authentifier un utilisateur"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user["password"]):
            return None
        
        # Retourner l'utilisateur sans le mot de passe
        user_copy = user.copy()
        del user_copy["password"]
        return user_copy
    
    def get_token(self, authorization: str = None) -> str:
        """Extraire le token de l'en-tête Authorization"""
        if not authorization:
            raise ValueError("Token manquant")
        
        if not authorization.startswith("Bearer "):
            raise ValueError("Format de token invalide")
        
        return authorization.split(" ")[1]
    
    def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """Récupérer l'utilisateur à partir du token"""
        user_id = self.verify_access_token(token)
        if not user_id:
            raise ValueError("Token invalide")
        
        user = self.users_db.get(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        # Retourner l'utilisateur sans le mot de passe
        user_copy = user.copy()
        if "password" in user_copy:
            del user_copy["password"]
        return user_copy