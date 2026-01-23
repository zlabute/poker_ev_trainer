"""
Tests for the equity cache service.
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.equity_cache import EquityCache, equity_cache


class TestEquityCache:
    """Tests for EquityCache class."""
    
    def setup_method(self):
        """Reset cache before each test."""
        # Create a fresh cache instance for testing
        self.cache = EquityCache.__new__(EquityCache)
        self.cache._initialized = False
        self.cache.__init__()
        self.cache.clear_all()
    
    def test_make_key(self):
        """Test cache key generation."""
        key = self.cache._make_key(
            game_id="game123",
            hole_cards=["As", "Kh"],
            community_cards=["Qd", "Jc", "Ts"]
        )
        
        # Key should contain all components
        assert "game123" in key
        assert "As" in key or "Kh" in key  # Sorted, so order might differ
        assert "Qd" in key
    
    def test_make_key_consistent(self):
        """Test that same inputs produce same key."""
        key1 = self.cache._make_key("g1", ["As", "Kh"], ["Qd"])
        key2 = self.cache._make_key("g1", ["As", "Kh"], ["Qd"])
        
        assert key1 == key2
    
    def test_make_key_hole_cards_sorted(self):
        """Test that hole cards order doesn't matter for key."""
        key1 = self.cache._make_key("g1", ["As", "Kh"], [])
        key2 = self.cache._make_key("g1", ["Kh", "As"], [])
        
        assert key1 == key2
    
    def test_make_key_community_order_matters(self):
        """Test that community cards order matters (board order is significant)."""
        key1 = self.cache._make_key("g1", ["As", "Kh"], ["Qd", "Jc"])
        key2 = self.cache._make_key("g1", ["As", "Kh"], ["Jc", "Qd"])
        
        # These should be different (board order matters)
        assert key1 != key2
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        self.cache.set(
            game_id="game1",
            hole_cards=["As", "Kh"],
            community_cards=[],
            num_opponents=3,
            equity=0.65
        )
        
        result = self.cache.get("game1", ["As", "Kh"], [], 3)
        
        assert result == 0.65
    
    def test_get_nonexistent(self):
        """Test getting a non-existent key returns None."""
        result = self.cache.get("nonexistent", ["2h", "3c"], [], 1)
        
        assert result is None
    
    def test_get_wrong_opponents(self):
        """Test that different opponent count returns None."""
        self.cache.set("g1", ["As", "Kh"], [], 3, 0.65)
        
        # Same hand but different opponent count
        result = self.cache.get("g1", ["As", "Kh"], [], 2)
        
        assert result is None
    
    def test_get_expired(self):
        """Test that expired entries return None."""
        self.cache.set("g1", ["As", "Kh"], [], 1, 0.65)
        
        # Manually expire the entry
        key = self.cache._make_key("g1", ["As", "Kh"], [])
        self.cache._cache[key].timestamp = time.time() - 400  # > 300s TTL
        
        result = self.cache.get("g1", ["As", "Kh"], [], 1)
        
        assert result is None
    
    def test_clear_game(self):
        """Test clearing all entries for a specific game."""
        self.cache.set("game1", ["As", "Kh"], [], 1, 0.65)
        self.cache.set("game1", ["As", "Kh"], ["Qd", "Jc", "Ts"], 1, 0.80)
        self.cache.set("game2", ["2h", "3c"], [], 1, 0.30)
        
        self.cache.clear_game("game1")
        
        assert self.cache.get("game1", ["As", "Kh"], [], 1) is None
        assert self.cache.get("game1", ["As", "Kh"], ["Qd", "Jc", "Ts"], 1) is None
        assert self.cache.get("game2", ["2h", "3c"], [], 1) == 0.30
    
    def test_clear_all(self):
        """Test clearing entire cache."""
        self.cache.set("game1", ["As", "Kh"], [], 1, 0.65)
        self.cache.set("game2", ["2h", "3c"], [], 1, 0.30)
        
        self.cache.clear_all()
        
        assert self.cache.get("game1", ["As", "Kh"], [], 1) is None
        assert self.cache.get("game2", ["2h", "3c"], [], 1) is None


class TestEquityCacheAsync:
    """Async tests for EquityCache."""
    
    def setup_method(self):
        """Reset cache before each test."""
        equity_cache.clear_all()
    
    @pytest.mark.asyncio
    async def test_precompute(self):
        """Test async precomputation."""
        await equity_cache.precompute(
            game_id="test_game",
            hole_cards=["As", "Ah"],
            community_cards=[],
            num_opponents=1,
            iterations=100  # Low iterations for speed
        )
        
        # Give it a moment to complete
        await asyncio.sleep(0.5)
        
        result = equity_cache.get("test_game", ["As", "Ah"], [], 1)
        
        # AA preflop should have high equity
        assert result is not None
        assert result > 0.7
    
    @pytest.mark.asyncio
    async def test_precompute_skips_if_cached(self):
        """Test that precompute doesn't recompute if already cached."""
        # Pre-populate cache
        equity_cache.set("g1", ["As", "Kh"], [], 1, 0.99)
        
        # Try to precompute same hand
        await equity_cache.precompute("g1", ["As", "Kh"], [], 1, 100)
        
        # Should still be our manually set value
        result = equity_cache.get("g1", ["As", "Kh"], [], 1)
        assert result == 0.99
    
    @pytest.mark.asyncio
    async def test_get_or_compute_cached(self):
        """Test get_or_compute returns cached value."""
        equity_cache.set("g1", ["As", "Kh"], [], 1, 0.77)
        
        result = await equity_cache.get_or_compute("g1", ["As", "Kh"], [], 1)
        
        assert result == 0.77
    
    @pytest.mark.asyncio
    async def test_get_or_compute_computes_if_missing(self):
        """Test get_or_compute calculates if not cached."""
        result = await equity_cache.get_or_compute(
            game_id="new_game",
            hole_cards=["7h", "2c"],
            community_cards=[],
            num_opponents=1,
            iterations=100
        )
        
        # 72o is a weak hand
        assert result is not None
        assert 0.2 < result < 0.5
        
        # Should now be cached
        cached = equity_cache.get("new_game", ["7h", "2c"], [], 1)
        assert cached == result
    
    @pytest.mark.asyncio
    async def test_parallel_precompute(self):
        """Test multiple parallel precomputations."""
        # Trigger multiple precomputes simultaneously
        tasks = [
            equity_cache.precompute(f"game{i}", ["As", "Ah"], [], 1, 100)
            for i in range(5)
        ]
        
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)  # Wait for all to complete
        
        # All should be cached
        for i in range(5):
            result = equity_cache.get(f"game{i}", ["As", "Ah"], [], 1)
            assert result is not None


class TestEquityCacheIntegration:
    """Integration tests with EVEvaluator."""
    
    def setup_method(self):
        equity_cache.clear_all()
    
    @pytest.mark.asyncio
    async def test_precompute_matches_direct_calculation(self):
        """Test that precomputed equity matches direct calculation."""
        from app.services.ev_evaluator import EVEvaluator
        
        hole_cards = ["Ks", "Qh"]
        community_cards = ["Js", "Ts", "2d"]
        num_opponents = 2
        iterations = 1000
        
        # Direct calculation
        direct_equity = EVEvaluator.calculate_equity(
            hole_cards, community_cards, num_opponents, iterations
        )
        
        # Precomputed
        await equity_cache.precompute(
            "test", hole_cards, community_cards, num_opponents, iterations
        )
        await asyncio.sleep(0.5)
        
        cached_equity = equity_cache.get("test", hole_cards, community_cards, num_opponents)
        
        # Should be reasonably close (Monte Carlo has variance)
        assert cached_equity is not None
        assert abs(direct_equity - cached_equity) < 0.15  # Within 15%
    
    def test_evaluate_user_action_uses_cached(self):
        """Test that evaluate_user_action uses cached equity."""
        from app.services.ev_evaluator import EVEvaluator
        
        hole_cards = ["As", "Kh"]
        community_cards = []
        cached_equity = 0.67  # Pre-set value
        
        result = EVEvaluator.evaluate_user_action(
            user_action="call",
            user_amount=20,
            hole_cards=hole_cards,
            community_cards=community_cards,
            pot=100,
            current_bet=20,
            player_bet=0,
            player_chips=1000,
            num_opponents=3,
            phase="preflop",
            available_actions=["fold", "call", "raise"],
            min_raise=40,
            cached_equity=cached_equity,  # Pass cached equity
        )
        
        # Should use our cached value
        assert result["equity"] == 0.67


class TestEquityCachePerformance:
    """Performance tests for equity cache."""
    
    def setup_method(self):
        equity_cache.clear_all()
    
    @pytest.mark.asyncio
    async def test_cache_hit_is_fast(self):
        """Test that cache hits are nearly instant."""
        # Populate cache
        equity_cache.set("g1", ["As", "Kh"], ["Qd", "Jc", "Ts"], 2, 0.85)
        
        # Time cache hit
        start = time.time()
        for _ in range(1000):
            equity_cache.get("g1", ["As", "Kh"], ["Qd", "Jc", "Ts"], 2)
        elapsed = time.time() - start
        
        # 1000 cache hits should take < 50ms
        assert elapsed < 0.05, f"Cache hits took {elapsed*1000:.0f}ms, expected < 50ms"
    
    @pytest.mark.asyncio
    async def test_cached_equity_faster_than_computing(self):
        """Test that using cached equity is much faster than computing."""
        hole_cards = ["As", "Ah"]
        community_cards = ["Kd", "Qc", "Jh"]
        
        # Time computation
        from app.services.ev_evaluator import EVEvaluator
        start = time.time()
        EVEvaluator.calculate_equity(hole_cards, community_cards, 3, 1000)
        compute_time = time.time() - start
        
        # Pre-cache the result
        equity_cache.set("perf_test", hole_cards, community_cards, 3, 0.75)
        
        # Time cache hit
        start = time.time()
        for _ in range(100):
            equity_cache.get("perf_test", hole_cards, community_cards, 3)
        cache_time = time.time() - start
        
        # Cache should be at least 100x faster
        assert cache_time * 100 < compute_time, (
            f"Cache ({cache_time*1000:.1f}ms for 100 hits) not significantly "
            f"faster than compute ({compute_time*1000:.0f}ms)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

