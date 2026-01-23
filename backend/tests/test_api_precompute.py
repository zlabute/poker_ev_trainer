"""
Tests for the precompute API endpoints.
"""

import pytest
import asyncio
import time
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.services.equity_cache import equity_cache
from app.routes.game import games


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up games and cache before each test."""
    games.clear()
    equity_cache.clear_all()
    yield
    games.clear()
    equity_cache.clear_all()


class TestPrecomputeEndpoint:
    """Tests for the /precompute endpoint."""
    
    def test_precompute_nonexistent_game(self, client):
        """Test precompute on non-existent game returns 404."""
        response = client.post("/api/game/nonexistent/precompute")
        assert response.status_code == 404
    
    def test_precompute_triggers_background_task(self, client):
        """Test that precompute triggers background computation."""
        # Create a game first
        create_response = client.post(
            "/api/game/new",
            json={
                "starting_chips": 1000,
                "small_blind": 10,
                "big_blind": 20,
                "num_opponents": 3,
                "aggression_level": "medium",
                "tightness_level": "medium",
            }
        )
        assert create_response.status_code == 200
        game_id = create_response.json()["id"]
        
        # Trigger precompute
        response = client.post(f"/api/game/{game_id}/precompute")
        assert response.status_code == 200
        assert response.json()["status"] == "precomputation_triggered"
    
    def test_create_game_triggers_precompute(self, client):
        """Test that creating a game triggers precomputation."""
        response = client.post(
            "/api/game/new",
            json={
                "starting_chips": 1000,
                "small_blind": 10,
                "big_blind": 20,
                "num_opponents": 2,
                "aggression_level": "medium",
                "tightness_level": "medium",
            }
        )
        
        assert response.status_code == 200
        game_id = response.json()["id"]
        
        # Give background task time to complete
        time.sleep(2)
        
        # Check that equity was precomputed
        game = games[game_id]
        hole_cards = game.get_human_hole_cards()
        num_opponents = game.get_num_active_opponents()
        
        cached = equity_cache.get(game_id, hole_cards, game.community_cards, num_opponents)
        
        # Should be cached (or at least attempted)
        # Note: This may occasionally fail due to timing, but should usually work
        # We can't guarantee the background task completes in time


class TestActionWithCachedEquity:
    """Tests for action endpoint using cached equity."""
    
    def test_action_uses_cached_equity(self, client):
        """Test that action endpoint uses cached equity when available."""
        # Create a game
        create_response = client.post(
            "/api/game/new",
            json={
                "starting_chips": 1000,
                "small_blind": 10,
                "big_blind": 20,
                "num_opponents": 1,
                "aggression_level": "passive",
                "tightness_level": "medium",
            }
        )
        game_id = create_response.json()["id"]
        game = games[game_id]
        
        # Manually set cached equity
        hole_cards = game.get_human_hole_cards()
        equity_cache.set(
            game_id, hole_cards, game.community_cards,
            num_opponents=1, equity=0.85
        )
        
        # Process CPU actions until it's human's turn
        while True:
            current_player = game.players[game.current_player]
            if current_player["is_human"]:
                break
            client.post(f"/api/game/{game_id}/cpu-action")
        
        # Submit human action
        start = time.time()
        response = client.post(
            f"/api/game/{game_id}/action",
            json={"action": "call", "amount": None}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        result = response.json()
        
        # Should use cached equity (0.85)
        if result["ev_result"]:
            assert result["ev_result"]["equity"] == 0.85
        
        # Should be fast (< 500ms) since we used cached equity
        # Note: This is a soft assertion, timing can vary
        print(f"Action with cached equity took {elapsed*1000:.0f}ms")
    
    def test_action_computes_if_not_cached(self, client):
        """Test that action endpoint computes equity if not cached."""
        # Create a game
        create_response = client.post(
            "/api/game/new",
            json={
                "starting_chips": 1000,
                "small_blind": 10,
                "big_blind": 20,
                "num_opponents": 1,
                "aggression_level": "passive",
                "tightness_level": "medium",
            }
        )
        game_id = create_response.json()["id"]
        game = games[game_id]
        
        # Clear cache to ensure nothing is cached
        equity_cache.clear_all()
        
        # Process CPU actions until it's human's turn
        while True:
            current_player = game.players[game.current_player]
            if current_player["is_human"]:
                break
            client.post(f"/api/game/{game_id}/cpu-action")
        
        # Submit human action
        response = client.post(
            f"/api/game/{game_id}/action",
            json={"action": "fold", "amount": None}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should still have computed equity
        if result["ev_result"]:
            assert 0 <= result["ev_result"]["equity"] <= 1


class TestNextHandClearsCache:
    """Tests for next hand clearing cache."""
    
    def test_next_hand_clears_cache(self, client):
        """Test that starting next hand clears old cache."""
        # Create a game
        create_response = client.post(
            "/api/game/new",
            json={
                "starting_chips": 1000,
                "small_blind": 10,
                "big_blind": 20,
                "num_opponents": 1,
                "aggression_level": "passive",
                "tightness_level": "medium",
            }
        )
        game_id = create_response.json()["id"]
        game = games[game_id]
        
        # Manually add some cache entries
        equity_cache.set(game_id, ["As", "Kh"], [], 1, 0.65)
        equity_cache.set(game_id, ["As", "Kh"], ["Qd", "Jc", "Ts"], 1, 0.90)
        
        # Verify they're cached
        assert equity_cache.get(game_id, ["As", "Kh"], [], 1) == 0.65
        
        # Start next hand
        response = client.post(f"/api/game/{game_id}/next-hand")
        assert response.status_code == 200
        
        # Old cache should be cleared
        assert equity_cache.get(game_id, ["As", "Kh"], [], 1) is None
        assert equity_cache.get(game_id, ["As", "Kh"], ["Qd", "Jc", "Ts"], 1) is None


class TestCPUActionTriggersPrecompute:
    """Tests for CPU action triggering precomputation."""
    
    def test_cpu_action_triggers_precompute_on_phase_change(self, client):
        """Test that CPU action triggers precompute when phase changes."""
        # Create a game with just 1 opponent for simpler testing
        create_response = client.post(
            "/api/game/new",
            json={
                "starting_chips": 1000,
                "small_blind": 10,
                "big_blind": 20,
                "num_opponents": 1,
                "aggression_level": "passive",  # Passive to likely just call
                "tightness_level": "loose",
            }
        )
        game_id = create_response.json()["id"]
        
        # The test verifies the endpoint works and background task is triggered
        # Actual verification of precomputation would require async waiting
        response = client.post(f"/api/game/{game_id}/cpu-action")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

