#!/usr/bin/env python3
"""
Script d'initialisation de la base de données PostgreSQL
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from database import init_database, close_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialise la base de données"""
    try:
        logger.info("Initialisation de la base de données PostgreSQL...")
        
        # Initialiser la base de données
        db_manager = await init_database()
        
        # Vérifier la santé
        health = await db_manager.health_check()
        logger.info(f"État de la base de données: {health}")
        
        # Fermer la connexion
        await close_database()
        
        logger.info("Initialisation terminée avec succès!")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())