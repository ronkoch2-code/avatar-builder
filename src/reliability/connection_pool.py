#!/usr/bin/env python3
"""
Connection Pool Module - Efficient connection management
=========================================================

Provides connection pooling for database and API connections with:
- Thread-safe connection management
- Connection health checking
- Automatic retry and reconnection
- Connection lifecycle management
- Pool size optimization
"""

import time
import logging
import threading
import queue
from typing import Optional, Any, Dict, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
from abc import ABC, abstractmethod
import weakref

# Import our reliability modules
from .error_handler import DatabaseError, NetworkError, AvatarEngineError
from .retry_manager import RetryConfig, global_retry_manager
from .circuit_breaker import CircuitBreakerConfig, global_circuit_manager

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic connections
T = TypeVar('T')


@dataclass
class PoolConfig:
    """Configuration for connection pool"""
    min_size: int = 1  # Minimum pool size
    max_size: int = 10  # Maximum pool size
    max_overflow: int = 5  # Additional connections beyond max_size
    timeout: float = 30.0  # Timeout for getting connection
    recycle: int = 3600  # Recycle connections after this many seconds
    echo: bool = False  # Log all pool events
    pre_ping: bool = True  # Test connections before using
    
    # Health check settings
    health_check_interval: float = 60.0  # Seconds between health checks
    max_retries: int = 3  # Max retries for failed connections
    retry_delay: float = 1.0  # Delay between retries
    
    # Connection validation
    validation_query: Optional[str] = None  # Query to validate connection
    validation_timeout: float = 5.0  # Timeout for validation query


@dataclass
class ConnectionInfo:
    """Information about a pooled connection"""
    connection: Any
    created_at: datetime
    last_used_at: datetime
    use_count: int = 0
    is_valid: bool = True
    pool_id: str = ""
    
    def age_seconds(self) -> float:
        """Get age of connection in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def idle_seconds(self) -> float:
        """Get idle time in seconds"""
        return (datetime.now() - self.last_used_at).total_seconds()


class ConnectionFactory(ABC):
    """Abstract factory for creating connections"""
    
    @abstractmethod
    def create_connection(self) -> Any:
        """Create a new connection"""
        pass
    
    @abstractmethod
    def validate_connection(self, connection: Any) -> bool:
        """Validate that connection is healthy"""
        pass
    
    @abstractmethod
    def close_connection(self, connection: Any) -> None:
        """Close a connection"""
        pass
    
    @abstractmethod
    def reset_connection(self, connection: Any) -> None:
        """Reset connection state for reuse"""
        pass


class Neo4jConnectionFactory(ConnectionFactory):
    """Factory for Neo4j database connections"""
    
    def __init__(self, uri: str, auth: tuple, **driver_config):
        self.uri = uri
        self.auth = auth
        self.driver_config = driver_config
    
    def create_connection(self) -> Any:
        """Create a new Neo4j session"""
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                self.uri,
                auth=self.auth,
                **self.driver_config
            )
            return driver.session()
        except Exception as e:
            raise DatabaseError(f"Failed to create Neo4j connection: {e}")
    
    def validate_connection(self, connection: Any) -> bool:
        """Validate Neo4j connection"""
        try:
            result = connection.run("RETURN 1 as test")
            result.single()
            return True
        except Exception:
            return False
    
    def close_connection(self, connection: Any) -> None:
        """Close Neo4j session"""
        try:
            connection.close()
        except Exception as e:
            logger.warning(f"Error closing Neo4j connection: {e}")
    
    def reset_connection(self, connection: Any) -> None:
        """Reset Neo4j session"""
        # Neo4j sessions don't need explicit reset
        pass


class HTTPConnectionFactory(ConnectionFactory):
    """Factory for HTTP connection sessions"""
    
    def __init__(self, base_url: str, timeout: float = 30.0, **session_config):
        self.base_url = base_url
        self.timeout = timeout
        self.session_config = session_config
    
    def create_connection(self) -> Any:
        """Create a new HTTP session"""
        try:
            import requests
            session = requests.Session()
            session.timeout = self.timeout
            for key, value in self.session_config.items():
                setattr(session, key, value)
            return session
        except Exception as e:
            raise NetworkError(f"Failed to create HTTP session: {e}")
    
    def validate_connection(self, connection: Any) -> bool:
        """Validate HTTP session"""
        try:
            # Test with a simple HEAD request
            response = connection.head(self.base_url, timeout=5)
            return response.status_code < 500
        except Exception:
            return False
    
    def close_connection(self, connection: Any) -> None:
        """Close HTTP session"""
        try:
            connection.close()
        except Exception as e:
            logger.warning(f"Error closing HTTP session: {e}")
    
    def reset_connection(self, connection: Any) -> None:
        """Reset HTTP session"""
        try:
            # Clear cookies and reset session
            connection.cookies.clear()
        except Exception as e:
            logger.warning(f"Error resetting HTTP session: {e}")


class ConnectionPool(Generic[T]):
    """
    Generic connection pool implementation
    
    Features:
    - Thread-safe connection management
    - Automatic connection validation
    - Connection recycling
    - Overflow connections
    - Health monitoring
    """
    
    def __init__(
        self,
        name: str,
        factory: ConnectionFactory,
        config: Optional[PoolConfig] = None
    ):
        self.name = name
        self.factory = factory
        self.config = config or PoolConfig()
        
        # Connection storage
        self._available = queue.Queue(maxsize=self.config.max_size)
        self._in_use: Dict[int, ConnectionInfo] = {}
        self._overflow_count = 0
        
        # Thread safety
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        
        # Statistics
        self.stats = {
            "connections_created": 0,
            "connections_destroyed": 0,
            "connections_recycled": 0,
            "get_wait_time_total": 0.0,
            "get_count": 0,
            "timeout_count": 0,
            "validation_failures": 0
        }
        
        # Health check thread
        self._health_check_thread = None
        self._stop_health_check = threading.Event()
        
        # Initialize minimum connections
        self._initialize_pool()
        
        # Start health check if configured
        if self.config.health_check_interval > 0:
            self._start_health_check()
    
    def _initialize_pool(self) -> None:
        """Initialize pool with minimum connections"""
        for _ in range(self.config.min_size):
            try:
                conn_info = self._create_connection()
                self._available.put(conn_info)
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")
    
    def _create_connection(self) -> ConnectionInfo:
        """Create a new connection"""
        connection = self.factory.create_connection()
        self.stats["connections_created"] += 1
        
        return ConnectionInfo(
            connection=connection,
            created_at=datetime.now(),
            last_used_at=datetime.now(),
            pool_id=f"{self.name}-{id(connection)}"
        )
    
    def _validate_connection(self, conn_info: ConnectionInfo) -> bool:
        """Validate a connection"""
        # Check age
        if self.config.recycle > 0 and conn_info.age_seconds() > self.config.recycle:
            logger.debug(f"Connection {conn_info.pool_id} expired (age)")
            return False
        
        # Check health if pre_ping enabled
        if self.config.pre_ping:
            try:
                is_valid = self.factory.validate_connection(conn_info.connection)
                if not is_valid:
                    self.stats["validation_failures"] += 1
                return is_valid
            except Exception as e:
                logger.debug(f"Connection validation failed: {e}")
                self.stats["validation_failures"] += 1
                return False
        
        return True
    
    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """
        Get a connection from the pool (context manager)
        
        Usage:
            with pool.get_connection() as conn:
                # Use connection
                pass
        """
        timeout = timeout or self.config.timeout
        conn_info = self._acquire_connection(timeout)
        
        try:
            yield conn_info.connection
        finally:
            self._release_connection(conn_info)
    
    def _acquire_connection(self, timeout: float) -> ConnectionInfo:
        """Acquire a connection from the pool"""
        start_time = time.time()
        deadline = start_time + timeout
        
        with self._lock:
            self.stats["get_count"] += 1
            
            while True:
                # Try to get available connection
                try:
                    conn_info = self._available.get_nowait()
                    
                    # Validate connection
                    if self._validate_connection(conn_info):
                        conn_info.last_used_at = datetime.now()
                        conn_info.use_count += 1
                        self._in_use[id(conn_info.connection)] = conn_info
                        
                        wait_time = time.time() - start_time
                        self.stats["get_wait_time_total"] += wait_time
                        
                        if self.config.echo:
                            logger.debug(f"Acquired connection {conn_info.pool_id}")
                        
                        return conn_info
                    else:
                        # Connection invalid, destroy it
                        self._destroy_connection(conn_info)
                        continue
                        
                except queue.Empty:
                    pass
                
                # Check if we can create new connection
                current_size = self._available.qsize() + len(self._in_use)
                
                if current_size < self.config.max_size:
                    # Create new connection
                    try:
                        conn_info = self._create_connection()
                        conn_info.last_used_at = datetime.now()
                        conn_info.use_count += 1
                        self._in_use[id(conn_info.connection)] = conn_info
                        
                        wait_time = time.time() - start_time
                        self.stats["get_wait_time_total"] += wait_time
                        
                        return conn_info
                    except Exception as e:
                        logger.error(f"Failed to create connection: {e}")
                        raise
                
                elif self._overflow_count < self.config.max_overflow:
                    # Create overflow connection
                    try:
                        conn_info = self._create_connection()
                        conn_info.last_used_at = datetime.now()
                        conn_info.use_count += 1
                        conn_info.is_valid = False  # Mark as overflow
                        self._in_use[id(conn_info.connection)] = conn_info
                        self._overflow_count += 1
                        
                        wait_time = time.time() - start_time
                        self.stats["get_wait_time_total"] += wait_time
                        
                        logger.info(f"Created overflow connection {conn_info.pool_id}")
                        return conn_info
                    except Exception as e:
                        logger.error(f"Failed to create overflow connection: {e}")
                        raise
                
                # Wait for connection to become available
                remaining = deadline - time.time()
                if remaining <= 0:
                    self.stats["timeout_count"] += 1
                    raise TimeoutError(f"Timeout waiting for connection from pool {self.name}")
                
                self._not_empty.wait(min(remaining, 1.0))
    
    def _release_connection(self, conn_info: ConnectionInfo) -> None:
        """Release a connection back to the pool"""
        with self._lock:
            # Remove from in-use
            conn_id = id(conn_info.connection)
            if conn_id in self._in_use:
                del self._in_use[conn_id]
            
            # Check if overflow connection
            if not conn_info.is_valid:
                self._destroy_connection(conn_info)
                self._overflow_count -= 1
                logger.info(f"Destroyed overflow connection {conn_info.pool_id}")
                return
            
            # Reset connection
            try:
                self.factory.reset_connection(conn_info.connection)
            except Exception as e:
                logger.warning(f"Failed to reset connection: {e}")
                self._destroy_connection(conn_info)
                return
            
            # Return to pool if healthy
            if self._validate_connection(conn_info):
                self._available.put(conn_info)
                self.stats["connections_recycled"] += 1
                
                if self.config.echo:
                    logger.debug(f"Released connection {conn_info.pool_id}")
                
                # Notify waiters
                self._not_empty.notify()
            else:
                self._destroy_connection(conn_info)
    
    def _destroy_connection(self, conn_info: ConnectionInfo) -> None:
        """Destroy a connection"""
        try:
            self.factory.close_connection(conn_info.connection)
            self.stats["connections_destroyed"] += 1
            
            if self.config.echo:
                logger.debug(f"Destroyed connection {conn_info.pool_id}")
        except Exception as e:
            logger.warning(f"Error destroying connection: {e}")
    
    def _start_health_check(self) -> None:
        """Start health check thread"""
        def health_check_loop():
            while not self._stop_health_check.is_set():
                try:
                    self._perform_health_check()
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                
                self._stop_health_check.wait(self.config.health_check_interval)
        
        self._health_check_thread = threading.Thread(
            target=health_check_loop,
            name=f"{self.name}-health-check",
            daemon=True
        )
        self._health_check_thread.start()
    
    def _perform_health_check(self) -> None:
        """Perform health check on idle connections"""
        with self._lock:
            # Check available connections
            checked = []
            
            while not self._available.empty():
                try:
                    conn_info = self._available.get_nowait()
                    
                    if self._validate_connection(conn_info):
                        checked.append(conn_info)
                    else:
                        self._destroy_connection(conn_info)
                        logger.info(f"Health check: removed invalid connection")
                except queue.Empty:
                    break
            
            # Return valid connections to pool
            for conn_info in checked:
                self._available.put(conn_info)
            
            # Ensure minimum pool size
            current_size = self._available.qsize() + len(self._in_use)
            while current_size < self.config.min_size:
                try:
                    conn_info = self._create_connection()
                    self._available.put(conn_info)
                    current_size += 1
                    logger.info(f"Health check: created connection to maintain min size")
                except Exception as e:
                    logger.warning(f"Health check: failed to create connection: {e}")
                    break
    
    def close(self) -> None:
        """Close the pool and all connections"""
        # Stop health check
        if self._health_check_thread:
            self._stop_health_check.set()
            self._health_check_thread.join(timeout=5)
        
        with self._lock:
            # Close in-use connections
            for conn_info in list(self._in_use.values()):
                self._destroy_connection(conn_info)
            self._in_use.clear()
            
            # Close available connections
            while not self._available.empty():
                try:
                    conn_info = self._available.get_nowait()
                    self._destroy_connection(conn_info)
                except queue.Empty:
                    break
            
            logger.info(f"Closed pool {self.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            avg_wait_time = (
                self.stats["get_wait_time_total"] / self.stats["get_count"]
                if self.stats["get_count"] > 0 else 0
            )
            
            return {
                **self.stats,
                "available_connections": self._available.qsize(),
                "in_use_connections": len(self._in_use),
                "overflow_connections": self._overflow_count,
                "average_wait_time": avg_wait_time,
                "timeout_rate": (
                    self.stats["timeout_count"] / self.stats["get_count"]
                    if self.stats["get_count"] > 0 else 0
                )
            }


class PoolManager:
    """Manages multiple connection pools"""
    
    def __init__(self):
        self.pools: Dict[str, ConnectionPool] = {}
        self._lock = threading.RLock()
        # Keep weak references to track pool usage
        self._pool_refs: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
    
    def create_pool(
        self,
        name: str,
        factory: ConnectionFactory,
        config: Optional[PoolConfig] = None
    ) -> ConnectionPool:
        """Create a new connection pool"""
        with self._lock:
            if name in self.pools:
                raise ValueError(f"Pool {name} already exists")
            
            pool = ConnectionPool(name, factory, config)
            self.pools[name] = pool
            self._pool_refs[name] = pool
            
            logger.info(f"Created pool {name}")
            return pool
    
    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get existing pool by name"""
        return self.pools.get(name)
    
    def close_pool(self, name: str) -> None:
        """Close and remove a pool"""
        with self._lock:
            if name in self.pools:
                pool = self.pools.pop(name)
                pool.close()
                logger.info(f"Closed and removed pool {name}")
    
    def close_all(self) -> None:
        """Close all pools"""
        with self._lock:
            for name in list(self.pools.keys()):
                self.close_pool(name)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools"""
        with self._lock:
            return {
                name: pool.get_stats()
                for name, pool in self.pools.items()
            }


# ============================================================================
# Global Pool Manager
# ============================================================================

global_pool_manager = PoolManager()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example 1: Neo4j connection pool
    neo4j_factory = Neo4jConnectionFactory(
        uri="bolt://localhost:7687",
        auth=("neo4j", "password")
    )
    
    neo4j_config = PoolConfig(
        min_size=2,
        max_size=10,
        max_overflow=5,
        recycle=3600,
        pre_ping=True
    )
    
    neo4j_pool = global_pool_manager.create_pool(
        "neo4j_main",
        neo4j_factory,
        neo4j_config
    )
    
    # Use connection from pool
    with neo4j_pool.get_connection() as conn:
        result = conn.run("MATCH (n) RETURN count(n) as count")
        print(f"Node count: {result.single()['count']}")
    
    # Example 2: HTTP connection pool
    http_factory = HTTPConnectionFactory(
        base_url="https://api.example.com",
        timeout=30.0
    )
    
    http_config = PoolConfig(
        min_size=1,
        max_size=5,
        pre_ping=True
    )
    
    http_pool = global_pool_manager.create_pool(
        "api_pool",
        http_factory,
        http_config
    )
    
    # Use HTTP session from pool
    with http_pool.get_connection() as session:
        response = session.get("https://api.example.com/data")
        print(f"API response: {response.status_code}")
    
    # Example 3: Get pool statistics
    stats = global_pool_manager.get_all_stats()
    print(f"Pool statistics: {stats}")
    
    # Cleanup
    global_pool_manager.close_all()
