"""
Gestionnaire de base de données PostgreSQL
"""

import os
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestionnaire de base de données PostgreSQL"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('POSTGRES_URL', 'postgresql://trading_user:secure_password@localhost:5432/cryptospreadedge')
        self.async_database_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
        
        # Engine synchrone pour les migrations
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        
        # Engine asynchrone pour les opérations
        self.async_engine = create_async_engine(
            self.async_database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        
        # Session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        self._initialized = False
    
    async def initialize(self):
        """Initialise la base de données"""
        if self._initialized:
            return
            
        try:
            # Tester la connexion
            await self.test_connection()
            
            # Créer les tables
            await self.create_tables()
            
            self._initialized = True
            logger.info("Base de données initialisée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur initialisation base de données: {e}")
            raise
    
    async def test_connection(self):
        """Teste la connexion à la base de données"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Connexion à PostgreSQL réussie")
        except Exception as e:
            logger.error(f"Erreur connexion PostgreSQL: {e}")
            raise
    
    async def create_tables(self):
        """Crée toutes les tables"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables créées avec succès")
        except Exception as e:
            logger.error(f"Erreur création tables: {e}")
            raise
    
    async def drop_tables(self):
        """Supprime toutes les tables (ATTENTION: destructif)"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.warning("Toutes les tables ont été supprimées")
        except Exception as e:
            logger.error(f"Erreur suppression tables: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Contexte manager pour obtenir une session asynchrone"""
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_sync_session(self) -> Session:
        """Obtient une session synchrone"""
        return self.SessionLocal()
    
    async def health_check(self) -> dict:
        """Vérifie la santé de la base de données"""
        try:
            async with self.get_session() as session:
                # Test de connexion
                result = await session.execute(text("SELECT 1 as health"))
                health = result.scalar()
                
                # Statistiques des tables
                stats = {}
                for table_name in ['orders', 'positions', 'trades', 'strategies']:
                    try:
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        stats[f"{table_name}_count"] = result.scalar()
                    except Exception:
                        stats[f"{table_name}_count"] = 0
                
                return {
                    "status": "healthy" if health == 1 else "unhealthy",
                    "database_url": self.database_url.split('@')[1] if '@' in self.database_url else "hidden",
                    "tables_stats": stats
                }
                
        except Exception as e:
            logger.error(f"Erreur health check: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self):
        """Ferme les connexions"""
        try:
            await self.async_engine.dispose()
            self.engine.dispose()
            logger.info("Connexions fermées")
        except Exception as e:
            logger.error(f"Erreur fermeture connexions: {e}")


# Instance globale
_database_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Obtient l'instance globale du gestionnaire de base de données"""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager


async def init_database():
    """Initialise la base de données globalement"""
    db_manager = get_database_manager()
    await db_manager.initialize()
    return db_manager


async def close_database():
    """Ferme la base de données globalement"""
    global _database_manager
    if _database_manager:
        await _database_manager.close()
        _database_manager = None