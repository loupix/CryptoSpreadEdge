"""
Système d'optimisation des performances pour CryptoSpreadEdge
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import uuid
from collections import defaultdict, deque

from sqlalchemy import text, select, func, Index
from sqlalchemy.ext.asyncio import AsyncSession
from .extended_models import Base

logger = logging.getLogger(__name__)


class IndexType(Enum):
    """Types d'index"""
    B_TREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    BRIN = "brin"


class QueryType(Enum):
    """Types de requêtes"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    ANALYZE = "analyze"
    VACUUM = "vacuum"


@dataclass
class QueryStats:
    """Statistiques de requête"""
    query_id: str
    query_text: str
    query_type: QueryType
    execution_time: float
    rows_affected: int
    execution_count: int
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    last_executed: datetime
    is_slow: bool = False
    metadata: Dict[str, Any] = None


@dataclass
class IndexRecommendation:
    """Recommandation d'index"""
    table_name: str
    column_names: List[str]
    index_type: IndexType
    reason: str
    estimated_benefit: float
    priority: int
    sql: str
    metadata: Dict[str, Any] = None


@dataclass
class PerformanceMetrics:
    """Métriques de performance"""
    timestamp: datetime
    total_queries: int
    slow_queries: int
    avg_execution_time: float
    max_execution_time: float
    cache_hit_ratio: float
    index_usage: float
    table_size: int
    index_size: int
    connection_count: int
    metadata: Dict[str, Any] = None


class PerformanceOptimizer:
    """Optimiseur de performances de base de données"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.query_stats: Dict[str, QueryStats] = {}
        self.performance_metrics: deque = deque(maxlen=1000)
        self.index_recommendations: List[IndexRecommendation] = []
        self.is_running = False
        
        # Configuration
        self.slow_query_threshold = 1.0  # secondes
        self.monitoring_interval = 60  # secondes
        self.optimization_interval = 3600  # secondes
        
        # Cache des requêtes
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # secondes
        
        # Statistiques de performance
        self.performance_counters = defaultdict(int)
        self.performance_timers = defaultdict(list)
    
    async def start(self):
        """Démarre l'optimiseur de performances"""
        self.is_running = True
        logger.info("Optimiseur de performances démarré")
        
        # Démarrer les tâches d'optimisation
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._optimization_loop())
        asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Arrête l'optimiseur de performances"""
        self.is_running = False
        logger.info("Optimiseur de performances arrêté")
    
    async def _monitoring_loop(self):
        """Boucle de monitoring des performances"""
        while self.is_running:
            try:
                # Collecter les métriques de performance
                await self._collect_performance_metrics()
                
                # Analyser les requêtes lentes
                await self._analyze_slow_queries()
                
                # Vérifier l'utilisation des index
                await self._check_index_usage()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Erreur monitoring performances: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _optimization_loop(self):
        """Boucle d'optimisation"""
        while self.is_running:
            try:
                # Générer des recommandations d'index
                await self._generate_index_recommendations()
                
                # Optimiser les requêtes
                await self._optimize_queries()
                
                # Nettoyer les données inutiles
                await self._cleanup_database()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(self.optimization_interval)
                
            except Exception as e:
                logger.error(f"Erreur optimisation: {e}")
                await asyncio.sleep(self.optimization_interval)
    
    async def _cleanup_loop(self):
        """Boucle de nettoyage"""
        while self.is_running:
            try:
                # Nettoyer les anciennes métriques
                await self._cleanup_old_metrics()
                
                # Nettoyer le cache des requêtes
                await self._cleanup_query_cache()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(3600)  # Nettoyer toutes les heures
                
            except Exception as e:
                logger.error(f"Erreur nettoyage: {e}")
                await asyncio.sleep(3600)
    
    async def _collect_performance_metrics(self):
        """Collecte les métriques de performance"""
        try:
            # Récupérer les statistiques de la base de données
            stats = await self._get_database_stats()
            
            # Calculer les métriques
            metrics = PerformanceMetrics(
                timestamp=datetime.utcnow(),
                total_queries=stats.get('total_queries', 0),
                slow_queries=stats.get('slow_queries', 0),
                avg_execution_time=stats.get('avg_execution_time', 0.0),
                max_execution_time=stats.get('max_execution_time', 0.0),
                cache_hit_ratio=stats.get('cache_hit_ratio', 0.0),
                index_usage=stats.get('index_usage', 0.0),
                table_size=stats.get('table_size', 0),
                index_size=stats.get('index_size', 0),
                connection_count=stats.get('connection_count', 0),
                metadata=stats
            )
            
            # Ajouter aux métriques
            self.performance_metrics.append(metrics)
            
            # Mettre à jour les compteurs
            self.performance_counters['total_queries'] += metrics.total_queries
            self.performance_counters['slow_queries'] += metrics.slow_queries
            
        except Exception as e:
            logger.error(f"Erreur collecte métriques performance: {e}")
    
    async def _get_database_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de la base de données"""
        try:
            stats = {}
            
            # Statistiques des requêtes
            query_stats = await self.db_session.execute(text("""
                SELECT 
                    count(*) as total_queries,
                    count(*) FILTER (WHERE mean_exec_time > 1000) as slow_queries,
                    avg(mean_exec_time) as avg_execution_time,
                    max(mean_exec_time) as max_execution_time
                FROM pg_stat_statements
            """))
            
            query_row = query_stats.first()
            if query_row:
                stats.update({
                    'total_queries': query_row.total_queries or 0,
                    'slow_queries': query_row.slow_queries or 0,
                    'avg_execution_time': float(query_row.avg_execution_time or 0),
                    'max_execution_time': float(query_row.max_execution_time or 0)
                })
            
            # Ratio de cache
            cache_stats = await self.db_session.execute(text("""
                SELECT 
                    sum(blks_hit) / (sum(blks_hit) + sum(blks_read)) as cache_hit_ratio
                FROM pg_stat_database
                WHERE datname = current_database()
            """))
            
            cache_row = cache_stats.first()
            if cache_row:
                stats['cache_hit_ratio'] = float(cache_row.cache_hit_ratio or 0)
            
            # Taille des tables et index
            size_stats = await self.db_session.execute(text("""
                SELECT 
                    sum(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
                    sum(pg_indexes_size(schemaname||'.'||tablename)) as index_size
                FROM pg_tables
                WHERE schemaname = 'public'
            """))
            
            size_row = size_stats.first()
            if size_row:
                stats.update({
                    'table_size': size_row.table_size or 0,
                    'index_size': size_row.index_size or 0
                })
            
            # Nombre de connexions
            conn_stats = await self.db_session.execute(text("""
                SELECT count(*) as connection_count
                FROM pg_stat_activity
                WHERE state = 'active'
            """))
            
            conn_row = conn_stats.first()
            if conn_row:
                stats['connection_count'] = conn_row.connection_count or 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur récupération statistiques base: {e}")
            return {}
    
    async def _analyze_slow_queries(self):
        """Analyse les requêtes lentes"""
        try:
            # Récupérer les requêtes lentes
            slow_queries = await self.db_session.execute(text("""
                SELECT 
                    query,
                    mean_exec_time,
                    calls,
                    total_exec_time,
                    rows,
                    shared_blks_hit,
                    shared_blks_read
                FROM pg_stat_statements
                WHERE mean_exec_time > :threshold
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """), {"threshold": self.slow_query_threshold * 1000})  # Convertir en millisecondes
            
            for row in slow_queries:
                query_id = str(uuid.uuid4())
                
                # Créer les statistiques de requête
                query_stats = QueryStats(
                    query_id=query_id,
                    query_text=row.query,
                    query_type=QueryType.SELECT,  # À déterminer dynamiquement
                    execution_time=row.mean_exec_time / 1000,  # Convertir en secondes
                    rows_affected=row.rows or 0,
                    execution_count=row.calls,
                    avg_execution_time=row.mean_exec_time / 1000,
                    min_execution_time=0,  # À calculer
                    max_execution_time=0,  # À calculer
                    last_executed=datetime.utcnow(),
                    is_slow=True,
                    metadata={
                        'total_exec_time': row.total_exec_time,
                        'shared_blks_hit': row.shared_blks_hit,
                        'shared_blks_read': row.shared_blks_read
                    }
                )
                
                self.query_stats[query_id] = query_stats
                
        except Exception as e:
            logger.error(f"Erreur analyse requêtes lentes: {e}")
    
    async def _check_index_usage(self):
        """Vérifie l'utilisation des index"""
        try:
            # Récupérer les statistiques d'utilisation des index
            index_stats = await self.db_session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
            """))
            
            unused_indexes = []
            for row in index_stats:
                if row.idx_scan == 0:
                    unused_indexes.append({
                        'table': f"{row.schemaname}.{row.tablename}",
                        'index': row.indexname,
                        'reason': 'Non utilisé'
                    })
            
            if unused_indexes:
                logger.warning(f"Index non utilisés détectés: {len(unused_indexes)}")
                
        except Exception as e:
            logger.error(f"Erreur vérification utilisation index: {e}")
    
    async def _generate_index_recommendations(self):
        """Génère des recommandations d'index"""
        try:
            recommendations = []
            
            # Analyser les requêtes lentes pour des recommandations
            for query_id, stats in self.query_stats.items():
                if not stats.is_slow:
                    continue
                
                # Analyser la requête pour des colonnes manquantes
                missing_indexes = await self._analyze_query_for_indexes(stats.query_text)
                
                for table, columns in missing_indexes.items():
                    recommendation = IndexRecommendation(
                        table_name=table,
                        column_names=columns,
                        index_type=IndexType.B_TREE,
                        reason=f"Améliorer les performances de la requête {query_id}",
                        estimated_benefit=stats.avg_execution_time * 0.5,  # Estimation
                        priority=1 if stats.avg_execution_time > 5.0 else 2,
                        sql=f"CREATE INDEX idx_{table}_{'_'.join(columns)} ON {table} ({', '.join(columns)})",
                        metadata={
                            'query_id': query_id,
                            'current_execution_time': stats.avg_execution_time
                        }
                    )
                    recommendations.append(recommendation)
            
            # Analyser les jointures pour des index composites
            join_recommendations = await self._analyze_joins_for_indexes()
            recommendations.extend(join_recommendations)
            
            # Trier par priorité
            recommendations.sort(key=lambda x: x.priority)
            
            self.index_recommendations = recommendations
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations index: {e}")
    
    async def _analyze_query_for_indexes(self, query_text: str) -> Dict[str, List[str]]:
        """Analyse une requête pour des index manquants"""
        try:
            # Analyse simplifiée - à améliorer avec un parser SQL
            missing_indexes = {}
            
            # Chercher les clauses WHERE
            if 'WHERE' in query_text.upper():
                # Extraire les colonnes dans WHERE
                where_clause = query_text.upper().split('WHERE')[1].split('ORDER BY')[0]
                
                # Chercher les noms de colonnes (simplifié)
                import re
                columns = re.findall(r'\b(\w+)\s*[=<>]', where_clause)
                
                if columns:
                    # Déterminer la table (simplifié)
                    table_match = re.search(r'FROM\s+(\w+)', query_text.upper())
                    if table_match:
                        table = table_match.group(1)
                        missing_indexes[table] = columns[:3]  # Limiter à 3 colonnes
            
            return missing_indexes
            
        except Exception as e:
            logger.error(f"Erreur analyse requête pour index: {e}")
            return {}
    
    async def _analyze_joins_for_indexes(self) -> List[IndexRecommendation]:
        """Analyse les jointures pour des index composites"""
        try:
            recommendations = []
            
            # Récupérer les statistiques de jointures
            join_stats = await self.db_session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE schemaname = 'public'
                ORDER BY n_distinct DESC
            """))
            
            # Analyser les colonnes avec haute cardinalité
            high_cardinality_columns = []
            for row in join_stats:
                if row.n_distinct > 1000:  # Seuil arbitraire
                    high_cardinality_columns.append({
                        'table': f"{row.schemaname}.{row.tablename}",
                        'column': row.attname,
                        'cardinality': row.n_distinct
                    })
            
            # Créer des recommandations pour les colonnes à haute cardinalité
            for col in high_cardinality_columns:
                recommendation = IndexRecommendation(
                    table_name=col['table'],
                    column_names=[col['column']],
                    index_type=IndexType.B_TREE,
                    reason=f"Colonne à haute cardinalité ({col['cardinality']})",
                    estimated_benefit=0.3,
                    priority=3,
                    sql=f"CREATE INDEX idx_{col['table']}_{col['column']} ON {col['table']} ({col['column']})",
                    metadata={
                        'cardinality': col['cardinality'],
                        'type': 'high_cardinality'
                    }
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erreur analyse jointures pour index: {e}")
            return []
    
    async def _optimize_queries(self):
        """Optimise les requêtes"""
        try:
            # Analyser les tables pour des statistiques à jour
            await self._update_table_statistics()
            
            # Optimiser les requêtes lentes
            await self._optimize_slow_queries()
            
            # Nettoyer les index inutiles
            await self._cleanup_unused_indexes()
            
        except Exception as e:
            logger.error(f"Erreur optimisation requêtes: {e}")
    
    async def _update_table_statistics(self):
        """Met à jour les statistiques des tables"""
        try:
            # Analyser toutes les tables
            await self.db_session.execute(text("ANALYZE"))
            logger.info("Statistiques des tables mises à jour")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour statistiques: {e}")
    
    async def _optimize_slow_queries(self):
        """Optimise les requêtes lentes"""
        try:
            # Appliquer les recommandations d'index prioritaires
            high_priority_recommendations = [
                r for r in self.index_recommendations 
                if r.priority == 1
            ]
            
            for recommendation in high_priority_recommendations[:5]:  # Limiter à 5
                try:
                    await self.db_session.execute(text(recommendation.sql))
                    logger.info(f"Index créé: {recommendation.sql}")
                except Exception as e:
                    logger.error(f"Erreur création index {recommendation.sql}: {e}")
            
        except Exception as e:
            logger.error(f"Erreur optimisation requêtes lentes: {e}")
    
    async def _cleanup_unused_indexes(self):
        """Nettoie les index inutilisés"""
        try:
            # Récupérer les index non utilisés
            unused_indexes = await self.db_session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                AND indexname NOT LIKE '%_pkey'
                AND indexname NOT LIKE '%_unique_%'
            """))
            
            for row in unused_indexes:
                try:
                    # Supprimer l'index
                    drop_sql = f"DROP INDEX {row.schemaname}.{row.indexname}"
                    await self.db_session.execute(text(drop_sql))
                    logger.info(f"Index supprimé: {drop_sql}")
                except Exception as e:
                    logger.error(f"Erreur suppression index {row.indexname}: {e}")
            
        except Exception as e:
            logger.error(f"Erreur nettoyage index inutilisés: {e}")
    
    async def _cleanup_database(self):
        """Nettoie la base de données"""
        try:
            # VACUUM des tables
            await self.db_session.execute(text("VACUUM ANALYZE"))
            logger.info("VACUUM ANALYZE exécuté")
            
        except Exception as e:
            logger.error(f"Erreur nettoyage base de données: {e}")
    
    async def _cleanup_old_metrics(self):
        """Nettoie les anciennes métriques"""
        try:
            # Garder seulement les métriques des dernières 24 heures
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Supprimer les anciennes métriques
            while (self.performance_metrics and 
                   self.performance_metrics[0].timestamp < cutoff_time):
                self.performance_metrics.popleft()
            
            # Supprimer les anciennes statistiques de requêtes
            old_query_ids = [
                qid for qid, stats in self.query_stats.items()
                if stats.last_executed < cutoff_time
            ]
            
            for qid in old_query_ids:
                del self.query_stats[qid]
            
        except Exception as e:
            logger.error(f"Erreur nettoyage anciennes métriques: {e}")
    
    async def _cleanup_query_cache(self):
        """Nettoie le cache des requêtes"""
        try:
            # Supprimer les entrées expirées du cache
            current_time = time.time()
            expired_keys = [
                key for key, (value, timestamp) in self.query_cache.items()
                if current_time - timestamp > self.cache_ttl
            ]
            
            for key in expired_keys:
                del self.query_cache[key]
            
        except Exception as e:
            logger.error(f"Erreur nettoyage cache requêtes: {e}")
    
    # Méthodes publiques
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Récupère un résumé des performances"""
        try:
            if not self.performance_metrics:
                return {}
            
            latest_metrics = self.performance_metrics[-1]
            
            return {
                "timestamp": latest_metrics.timestamp,
                "total_queries": latest_metrics.total_queries,
                "slow_queries": latest_metrics.slow_queries,
                "avg_execution_time": latest_metrics.avg_execution_time,
                "max_execution_time": latest_metrics.max_execution_time,
                "cache_hit_ratio": latest_metrics.cache_hit_ratio,
                "index_usage": latest_metrics.index_usage,
                "table_size_mb": latest_metrics.table_size / (1024 * 1024),
                "index_size_mb": latest_metrics.index_size / (1024 * 1024),
                "connection_count": latest_metrics.connection_count,
                "slow_query_percentage": (latest_metrics.slow_queries / latest_metrics.total_queries * 100) if latest_metrics.total_queries > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Erreur résumé performances: {e}")
            return {}
    
    async def get_slow_queries(self, limit: int = 10) -> List[QueryStats]:
        """Récupère les requêtes lentes"""
        try:
            slow_queries = [
                stats for stats in self.query_stats.values()
                if stats.is_slow
            ]
            
            # Trier par temps d'exécution
            slow_queries.sort(key=lambda x: x.avg_execution_time, reverse=True)
            
            return slow_queries[:limit]
            
        except Exception as e:
            logger.error(f"Erreur récupération requêtes lentes: {e}")
            return []
    
    async def get_index_recommendations(self) -> List[IndexRecommendation]:
        """Récupère les recommandations d'index"""
        return self.index_recommendations.copy()
    
    async def apply_index_recommendation(self, recommendation_id: int) -> bool:
        """Applique une recommandation d'index"""
        try:
            if 0 <= recommendation_id < len(self.index_recommendations):
                recommendation = self.index_recommendations[recommendation_id]
                
                await self.db_session.execute(text(recommendation.sql))
                await self.db_session.commit()
                
                logger.info(f"Recommandation d'index appliquée: {recommendation.sql}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur application recommandation index: {e}")
            return False
    
    async def get_query_plan(self, query_text: str) -> Dict[str, Any]:
        """Récupère le plan d'exécution d'une requête"""
        try:
            # Utiliser EXPLAIN pour obtenir le plan
            explain_result = await self.db_session.execute(
                text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_text}")
            )
            
            plan_row = explain_result.first()
            if plan_row:
                return plan_row[0][0]  # Le plan est dans le premier élément
            
            return {}
            
        except Exception as e:
            logger.error(f"Erreur récupération plan requête: {e}")
            return {}
    
    async def optimize_table(self, table_name: str) -> bool:
        """Optimise une table spécifique"""
        try:
            # Analyser la table
            await self.db_session.execute(text(f"ANALYZE {table_name}"))
            
            # VACUUM la table
            await self.db_session.execute(text(f"VACUUM {table_name}"))
            
            # REINDEX si nécessaire
            await self.db_session.execute(text(f"REINDEX TABLE {table_name}"))
            
            logger.info(f"Table {table_name} optimisée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur optimisation table {table_name}: {e}")
            return False
    
    async def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Récupère les statistiques d'une table"""
        try:
            # Taille de la table
            size_result = await self.db_session.execute(text(f"""
                SELECT 
                    pg_size_pretty(pg_total_relation_size('{table_name}')) as size,
                    pg_total_relation_size('{table_name}') as size_bytes
            """))
            
            size_row = size_result.first()
            
            # Statistiques de la table
            stats_result = await self.db_session.execute(text(f"""
                SELECT 
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE relname = '{table_name}'
            """))
            
            stats_row = stats_result.first()
            
            return {
                "table_name": table_name,
                "size": size_row.size if size_row else "N/A",
                "size_bytes": size_row.size_bytes if size_row else 0,
                "inserts": stats_row.inserts if stats_row else 0,
                "updates": stats_row.updates if stats_row else 0,
                "deletes": stats_row.deletes if stats_row else 0,
                "live_tuples": stats_row.live_tuples if stats_row else 0,
                "dead_tuples": stats_row.dead_tuples if stats_row else 0,
                "last_vacuum": stats_row.last_vacuum if stats_row else None,
                "last_autovacuum": stats_row.last_autovacuum if stats_row else None,
                "last_analyze": stats_row.last_analyze if stats_row else None,
                "last_autoanalyze": stats_row.last_autoanalyze if stats_row else None
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération statistiques table {table_name}: {e}")
            return {}
    
    async def set_slow_query_threshold(self, threshold: float):
        """Définit le seuil des requêtes lentes"""
        self.slow_query_threshold = threshold
        logger.info(f"Seuil des requêtes lentes défini à {threshold} secondes")
    
    async def get_performance_history(self, hours: int = 24) -> List[PerformanceMetrics]:
        """Récupère l'historique des performances"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            return [
                metrics for metrics in self.performance_metrics
                if metrics.timestamp >= cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Erreur récupération historique performances: {e}")
            return []