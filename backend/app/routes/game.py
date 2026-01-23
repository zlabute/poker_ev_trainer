"""
Game API routes.
"""

import asyncio
from typing import Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..models import (
    GameSettings,
    GameState,
    ActionRequest,
    ActionResponse,
    EVResult,
)
from ..services import PokerGame, EVEvaluator, CPUPlayer, equity_cache

router = APIRouter()

# In-memory game storage (for simplicity)
games: Dict[str, PokerGame] = {}


async def trigger_precomputation(game: PokerGame):
    """Trigger background precomputation for the human player's equity."""
    try:
        hole_cards = game.get_human_hole_cards()
        if not hole_cards or len(hole_cards) < 2:
            return
        
        num_opponents = game.get_num_active_opponents()
        
        # Precompute equity in background
        await equity_cache.precompute(
            game_id=game.id,
            hole_cards=hole_cards,
            community_cards=game.community_cards,
            num_opponents=num_opponents,
            iterations=2000
        )
    except Exception as e:
        print(f"Precomputation trigger error: {e}")


@router.post("/new", response_model=GameState)
async def create_game(settings: GameSettings, background_tasks: BackgroundTasks):
    """Create a new game session."""
    game = PokerGame(settings)
    game.start_hand()
    games[game.id] = game
    
    # Trigger precomputation in background
    background_tasks.add_task(trigger_precomputation, game)
    
    return game.get_state()


@router.post("/{game_id}/precompute")
async def precompute_equity(game_id: str, background_tasks: BackgroundTasks):
    """
    Trigger precomputation of equity for the current game state.
    Frontend should call this when it's the human's turn to ensure equity is ready.
    """
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    background_tasks.add_task(trigger_precomputation, game)
    
    return {"status": "precomputation_triggered"}


@router.get("/{game_id}", response_model=GameState)
async def get_game(game_id: str):
    """Get current game state."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[game_id].get_state()


@router.post("/{game_id}/action", response_model=ActionResponse)
async def submit_action(game_id: str, action_request: ActionRequest):
    """Submit a player action and get EV evaluation."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    # Verify it's human's turn
    current = game.players[game.current_player]
    if not current["is_human"]:
        raise HTTPException(status_code=400, detail="Not human player's turn")
    
    # Get hole cards for evaluation
    hole_cards = game.get_human_hole_cards()
    num_opponents = game.get_num_active_opponents()
    
    # Try to get cached equity first
    cached_equity = equity_cache.get(
        game_id, hole_cards, game.community_cards, num_opponents
    )
    
    # Evaluate the action using EVEvaluator with cached equity if available
    ev_result_dict = EVEvaluator.evaluate_user_action(
        user_action=action_request.action,
        user_amount=action_request.amount,
        hole_cards=hole_cards,
        community_cards=game.community_cards,
        pot=game.pot,
        current_bet=game.current_bet,
        player_bet=current["current_bet"],
        player_chips=current["chips"],
        num_opponents=num_opponents,
        phase=game.phase,
        available_actions=game._get_available_actions(),
        min_raise=game.current_bet + game.big_blind,
        cached_equity=cached_equity,  # Pass cached equity
    )
    
    ev_result = EVResult(**ev_result_dict)
    
    # Apply the action
    success = game.apply_action(action_request.action, action_request.amount)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    # Check if all-in runout is needed
    if game.is_all_in_runout_needed():
        game.run_out_board()
    
    # Check if hand is complete
    hand_complete = False
    winner_id = None
    
    if game.phase == "showdown" or len(game._get_active_players()) <= 1:
        hand_complete = True
        winner_id = game.get_winner()
        if winner_id:
            game.award_pot(winner_id)
    
    return ActionResponse(
        success=True,
        ev_result=ev_result,
        game_state=game.get_state(),
        hand_complete=hand_complete,
        winner_id=winner_id,
    )


@router.post("/{game_id}/cpu-action", response_model=GameState)
async def cpu_action(game_id: str, background_tasks: BackgroundTasks):
    """Execute CPU player's action."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    previous_phase = game.phase
    previous_community = list(game.community_cards)
    
    # Check if all-in runout is needed first
    if game.is_all_in_runout_needed():
        game.run_out_board()
        # Award pot after runout
        winner_id = game.get_winner()
        if winner_id:
            game.award_pot(winner_id)
        return game.get_state()
    
    # Check if hand is already complete
    if game.phase == "showdown" or len(game._get_active_players()) <= 1:
        winner_id = game.get_winner()
        if winner_id:
            game.award_pot(winner_id)
        return game.get_state()
    
    # Verify it's CPU's turn
    current = game.players[game.current_player]
    if current["is_human"]:
        raise HTTPException(status_code=400, detail="Not CPU player's turn")
    
    if current["is_folded"] or current["is_all_in"]:
        # Skip to next player if this CPU can't act
        game._skip_to_next_player()
        return game.get_state()
    
    # Get CPU's hole cards
    hole_cards = current["hole_cards"]
    num_opponents = len([
        p for p in game.players 
        if p["id"] != current["id"] and not p["is_folded"] and p["is_active"]
    ])
    
    # CPU decides action using EVEvaluator equity
    action, amount = CPUPlayer.decide_action(
        hole_cards=hole_cards,
        community_cards=game.community_cards,
        pot=game.pot,
        current_bet=game.current_bet,
        player_bet=current["current_bet"],
        player_chips=current["chips"],
        num_opponents=num_opponents,
        phase=game.phase,
        available_actions=game._get_available_actions(),
        min_raise=game.current_bet + game.big_blind,
        aggression=current["aggression"],  # Each CPU has unique aggression
        tightness=current["tightness"],  # Each CPU has unique tightness
    )
    
    # Apply the action
    game.apply_action(action, amount)
    
    # Check if all-in runout is needed after action
    if game.is_all_in_runout_needed():
        game.run_out_board()
    
    # Check if hand is complete after CPU action
    if game.phase == "showdown" or len(game._get_active_players()) <= 1:
        winner_id = game.get_winner()
        if winner_id:
            game.award_pot(winner_id)
    
    # If phase changed or community cards changed, trigger precomputation
    # for when it's the human's turn next
    if game.phase != previous_phase or game.community_cards != previous_community:
        background_tasks.add_task(trigger_precomputation, game)
    
    return game.get_state()


@router.post("/{game_id}/next-hand", response_model=GameState)
async def next_hand(game_id: str, background_tasks: BackgroundTasks):
    """Start the next hand."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    # Clear old equity cache for this game
    equity_cache.clear_game(game_id)
    
    game.next_hand()
    game.start_hand()
    
    # Trigger precomputation for new hand
    background_tasks.add_task(trigger_precomputation, game)
    
    return game.get_state()


@router.delete("/{game_id}")
async def delete_game(game_id: str):
    """End a game session."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    del games[game_id]
    return {"message": "Game deleted", "game_id": game_id}

