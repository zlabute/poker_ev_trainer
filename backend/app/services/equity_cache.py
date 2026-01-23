"""
Equity Cache Service with background precomputation.
Precomputes equity calculations in the background to reduce wait times.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from time import time

from .ev_evaluator import EVEvaluator


@dataclass
class CachedEquity:
    """Cached equity calculation result."""
    equity: float
    timestamp: float
    num_opponents: int


class EquityCache:
    """
    Thread-safe equity cache with background precomputation.
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Cache: {(game_id, hole_cards_str, community_cards_str): CachedEquity}
        self._cache: Dict[str, CachedEquity] = {}
        
        # Thread pool for parallel computation
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Track pending computations to avoid duplicates
        self._pending: set = set()
        
        # Cache TTL in seconds (equity can change between phases)
        self._ttl = 300  # 5 minutes
        
        self._initialized = True
    
    def _make_key(
        self, 
        game_id: str, 
        hole_cards: List[str], 
        community_cards: List[str]
    ) -> str:
        """Create a cache key from game state."""
        hole_str = ','.join(sorted(hole_cards))
        comm_str = ','.join(community_cards)  # Order matters for board
        return f"{game_id}:{hole_str}:{comm_str}"
    
    def get(
        self, 
        game_id: str, 
        hole_cards: List[str], 
        community_cards: List[str],
        num_opponents: int
    ) -> Optional[float]:
        """
        Get cached equity if available and valid.
        Returns None if not cached or expired.
        """
        key = self._make_key(game_id, hole_cards, community_cards)
        
        if key in self._cache:
            cached = self._cache[key]
            # Check if still valid (same opponents and not expired)
            if (cached.num_opponents == num_opponents and 
                time() - cached.timestamp < self._ttl):
                return cached.equity
        
        return None
    
    def set(
        self, 
        game_id: str, 
        hole_cards: List[str], 
        community_cards: List[str],
        num_opponents: int,
        equity: float
    ):
        """Store equity in cache."""
        key = self._make_key(game_id, hole_cards, community_cards)
        self._cache[key] = CachedEquity(
            equity=equity,
            timestamp=time(),
            num_opponents=num_opponents
        )
        # Remove from pending if it was there
        self._pending.discard(key)
    
    def _compute_equity_sync(
        self,
        hole_cards: List[str],
        community_cards: List[str],
        num_opponents: int,
        iterations: int = 2000
    ) -> float:
        """Synchronous equity computation (runs in thread pool)."""
        return EVEvaluator.calculate_equity(
            hole_cards,
            community_cards,
            num_opponents,
            iterations
        )
    
    async def precompute(
        self,
        game_id: str,
        hole_cards: List[str],
        community_cards: List[str],
        num_opponents: int,
        iterations: int = 2000
    ):
        """
        Precompute equity in background thread.
        Non-blocking - returns immediately.
        """
        key = self._make_key(game_id, hole_cards, community_cards)
        
        # Skip if already cached or pending
        if key in self._cache or key in self._pending:
            return
        
        self._pending.add(key)
        
        # Run computation in thread pool
        loop = asyncio.get_event_loop()
        try:
            equity = await loop.run_in_executor(
                self._executor,
                self._compute_equity_sync,
                hole_cards,
                community_cards,
                num_opponents,
                iterations
            )
            self.set(game_id, hole_cards, community_cards, num_opponents, equity)
        except Exception as e:
            print(f"Precomputation error: {e}")
            self._pending.discard(key)
    
    async def get_or_compute(
        self,
        game_id: str,
        hole_cards: List[str],
        community_cards: List[str],
        num_opponents: int,
        iterations: int = 2000
    ) -> float:
        """
        Get cached equity or compute if not available.
        This is a blocking call that waits for computation.
        """
        # Check cache first
        cached = self.get(game_id, hole_cards, community_cards, num_opponents)
        if cached is not None:
            return cached
        
        # Compute in background thread
        loop = asyncio.get_event_loop()
        equity = await loop.run_in_executor(
            self._executor,
            self._compute_equity_sync,
            hole_cards,
            community_cards,
            num_opponents,
            iterations
        )
        
        # Cache the result
        self.set(game_id, hole_cards, community_cards, num_opponents, equity)
        
        return equity
    
    def clear_game(self, game_id: str):
        """Clear all cached entries for a game."""
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{game_id}:")]
        for key in keys_to_remove:
            del self._cache[key]
        
        # Also clear pending
        pending_to_remove = [k for k in self._pending if k.startswith(f"{game_id}:")]
        for key in pending_to_remove:
            self._pending.discard(key)
    
    def clear_all(self):
        """Clear entire cache."""
        self._cache.clear()
        self._pending.clear()


# Global singleton instance
equity_cache = EquityCache()

