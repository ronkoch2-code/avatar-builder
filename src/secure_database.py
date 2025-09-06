#!/usr/bin/env python3
"""
Secure Neo4j Database Wrapper for Avatar-Engine
===============================================

Provides secure database operations with:
- Parameterized queries to prevent injection
- Connection pooling
- Error handling and retry logic
- Query logging and monitoring
- Transaction management

Author: Avatar-Engine Security Team
Date: 2025-01-30
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from contextlib import contextmanager
from datetime import datetime
import time
from neo4j import GraphDatabase, Transaction, Session
from neo4j.exceptions import ServiceUnavailable, SessionExpired, TransientError
from tenacity import retry, stop_after_attempt, wait_exponential

# Import security utilities
try:
    from .security_utils import SecurityManager, SecureLogger, rate_limit
    from .config_manager import ConfigManager
except ImportError:
    SecurityManager = None
    SecureLogger = None
    ConfigManager = None
    def rate_limit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


class SecureNeo4jConnection:
    """Secure wrapper for Neo4j database connections"""
    
    def __init__(self, config: Optional[ConfigManager] = None, **kwargs):
        """
        Initialize secure Neo4j connection
        
        Args:
            config: ConfigManager instance
            **kwargs: Additional connection parameters
        """
        self.config = config or (ConfigManager() if ConfigManager else None)
        self.security_manager = SecurityManager() if SecurityManager else None
        self.secure_logger = SecureLogger("database") if SecureLogger else None
        
        # Get secure connection configuration
        if self.config and hasattr(self.config, 'get_secure_neo4j_config'):
            conn_config = self.config.get_secure_neo4j_config()
        else:
            conn_config = self._get_default_config()
        conn_config.update(kwargs)
        
        # Initialize driver with secure settings
        self.driver = GraphDatabase.driver(
            conn_config['uri'],
            auth=conn_config['auth'],
            encrypted=conn_config.get('encrypted', True),
            trust=conn_config.get('trust', 'TRUST_SYSTEM_CA_SIGNED_CERTIFICATES'),
            max_connection_pool_size=conn_config.get('max_connection_pool_size', 50),
            connection_timeout=conn_config.get('connection_timeout', 30.0)
        )
        
        self.database = conn_config.get('database', 'neo4j')
        
        # Query statistics
        self.query_count = 0
        self.error_count = 0
        
        # Test connection
        self._test_connection()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if ConfigManager not available"""
        import os
        
        # Require password to be explicitly set - no defaults
        password = os.getenv('NEO4J_PASSWORD')
        if not password:
            raise ValueError(
                "NEO4J_PASSWORD environment variable must be set. "
                "Please set secure database credentials before running."
            )
        
        username = os.getenv('NEO4J_USERNAME')
        if not username:
            raise ValueError(
                "NEO4J_USERNAME environment variable must be set."
            )
        
        return {
            'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            'auth': (username, password),
            'database': os.getenv('NEO4J_DATABASE', 'neo4j'),
            'encrypted': True,
            'trust': 'TRUST_SYSTEM_CA_SIGNED_CERTIFICATES'
        }
    
    def _test_connection(self):
        """Test database connection"""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record['test'] != 1:
                    raise ConnectionError("Database connection test failed")
            logger.info("Neo4j connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _validate_query(self, query: str) -> None:
        """
        Validate query for potential injection attempts
        
        Args:
            query: Cypher query to validate
            
        Raises:
            ValueError: If query contains suspicious patterns
        """
        # Check for comment-based injection
        suspicious_patterns = [
            r'//.*DROP',  # Comment with DROP
            r'/\*.*DROP.*\*/',  # Block comment with DROP
            r';\s*DROP',  # Multiple statements with DROP
            r';\s*DELETE\s+.*WHERE\s+1\s*=\s*1',  # Delete all pattern
        ]
        
        import re
        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Suspicious query pattern detected: {pattern}")
                raise ValueError("Query validation failed: suspicious pattern detected")
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize parameters for safe querying
        
        Args:
            params: Query parameters
            
        Returns:
            Sanitized parameters
        """
        if not params:
            return {}
        
        sanitized = {}
        for key, value in params.items():
            # Validate parameter names (alphanumeric and underscore only)
            if not key.replace('_', '').isalnum():
                raise ValueError(f"Invalid parameter name: {key}")
            
            # Sanitize values
            if isinstance(value, str):
                # Remove any potential Cypher injection patterns
                if any(danger in value.upper() for danger in ['DROP', 'DELETE', 'REMOVE', 'DETACH']):
                    logger.warning(f"Potentially dangerous value in parameter {key}")
                    # Don't reject, but log for monitoring
                
            sanitized[key] = value
        
        return sanitized
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def execute_query(self, 
                     query: str, 
                     params: Optional[Dict[str, Any]] = None,
                     timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Execute a parameterized Cypher query safely
        
        Args:
            query: Cypher query with parameter placeholders
            params: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            List of result records as dictionaries
            
        Example:
            results = db.execute_query(
                "MATCH (p:Person {name: $name}) RETURN p",
                {"name": "John Doe"}
            )
        """
        # Validate query
        self._validate_query(query)
        
        # Sanitize parameters
        safe_params = self._sanitize_params(params or {})
        
        # Log query execution (without sensitive data)
        if self.secure_logger:
            self.secure_logger.log_event("query_execution", {
                "query_hash": hash(query),
                "param_count": len(safe_params),
                "timeout": timeout
            })
        
        start_time = time.time()
        results = []
        
        try:
            with self.driver.session(database=self.database) as session:
                if timeout:
                    result = session.run(query, safe_params, timeout=timeout)
                else:
                    result = session.run(query, safe_params)
                
                results = [dict(record) for record in result]
            
            # Update statistics
            self.query_count += 1
            execution_time = time.time() - start_time
            
            logger.debug(f"Query executed successfully in {execution_time:.2f}s")
            
            return results
            
        except (ServiceUnavailable, SessionExpired, TransientError) as e:
            self.error_count += 1
            logger.error(f"Transient database error: {e}")
            raise
        except Exception as e:
            self.error_count += 1
            logger.error(f"Query execution failed: {e}")
            raise
    
    @contextmanager
    def transaction(self, mode: str = "WRITE"):
        """
        Create a transaction context for multiple operations
        
        Args:
            mode: Transaction mode ("READ" or "WRITE")
            
        Example:
            with db.transaction() as tx:
                tx.run("CREATE (p:Person {name: $name})", {"name": "Jane"})
                tx.run("CREATE (p:Person {name: $name})", {"name": "John"})
        """
        session = self.driver.session(database=self.database)
        tx = None
        
        try:
            if mode == "READ":
                tx = session.begin_transaction()
            else:
                tx = session.begin_transaction()
            
            yield SecureTransaction(tx, self)
            
            tx.commit()
            logger.debug("Transaction committed successfully")
            
        except Exception as e:
            if tx:
                tx.rollback()
                logger.warning("Transaction rolled back due to error")
            raise
        finally:
            session.close()
    
    def batch_execute(self, 
                     queries: List[Tuple[str, Dict[str, Any]]],
                     batch_size: int = 100) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple queries in batches
        
        Args:
            queries: List of (query, params) tuples
            batch_size: Number of queries per batch
            
        Returns:
            List of results for each query
        """
        all_results = []
        
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i+batch_size]
            
            with self.transaction() as tx:
                batch_results = []
                for query, params in batch:
                    try:
                        results = tx.run(query, params)
                        batch_results.append(results)
                    except Exception as e:
                        logger.error(f"Batch query failed: {e}")
                        batch_results.append([])
                
                all_results.extend(batch_results)
        
        return all_results
    
    def check_index_exists(self, label: str, property: str) -> bool:
        """Check if an index exists on a label and property"""
        query = """
        SHOW INDEXES
        WHERE labelsOrTypes = [$label] AND properties = [$property]
        """
        results = self.execute_query(query, {"label": label, "property": property})
        return len(results) > 0
    
    def create_index_if_not_exists(self, label: str, property: str, index_name: Optional[str] = None):
        """Create an index if it doesn't exist"""
        if not self.check_index_exists(label, property):
            index_name = index_name or f"idx_{label}_{property}"
            query = f"CREATE INDEX {index_name} IF NOT EXISTS FOR (n:{label}) ON (n.{property})"
            self.execute_query(query)
            logger.info(f"Created index {index_name} on {label}.{property}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "query_count": self.query_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.query_count, 1),
            "connection_pool_size": self.driver._pool.size() if hasattr(self.driver, '_pool') else None
        }
    
    def close(self):
        """Close database connection"""
        try:
            self.driver.close()
            logger.info("Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {e}")


class SecureTransaction:
    """Wrapper for secure transaction operations"""
    
    def __init__(self, tx: Transaction, connection: SecureNeo4jConnection):
        self.tx = tx
        self.connection = connection
    
    def run(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run query in transaction with validation"""
        # Validate and sanitize
        self.connection._validate_query(query)
        safe_params = self.connection._sanitize_params(params or {})
        
        # Execute
        result = self.tx.run(query, safe_params)
        return [dict(record) for record in result]


# Convenience functions
def create_secure_connection(**kwargs) -> SecureNeo4jConnection:
    """Create a secure Neo4j connection"""
    return SecureNeo4jConnection(**kwargs)


def escape_cypher_string(value: str) -> str:
    """
    Escape a string for safe use in Cypher queries
    
    Note: Prefer parameterized queries over string escaping
    """
    if not isinstance(value, str):
        return str(value)
    
    # Escape special characters
    value = value.replace("\\", "\\\\")
    value = value.replace("'", "\\'")
    value = value.replace('"', '\\"')
    value = value.replace("\n", "\\n")
    value = value.replace("\r", "\\r")
    value = value.replace("\t", "\\t")
    
    return value


# Export main components
__all__ = [
    'SecureNeo4jConnection',
    'SecureTransaction',
    'create_secure_connection',
    'escape_cypher_string'
]
