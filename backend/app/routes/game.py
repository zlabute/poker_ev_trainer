"""
Game API routes.
"""

import asyncio
from typing import Dict
from fastapi import APIRouter, HTTPException

from ..models import (
    GameSettings,
    GameState,
    ActionRequest,
    ActionResponse,
    EVResult,
)
from ..services import PokerGame, EVEvaluator, CPUPlayer

router = APIRouter()

# In-memory game storage (for simplicity)
games: Dict[str, PokerGame] = {}


@router.post("/new", response_model=GameState)
async def create_game(settings: GameSettings):
    """Create a new game session."""
    game = PokerGame(settings)
    game.start_hand()
    games[game.id] = game
    return game.get_state()


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
    
    # Evaluate the action using PokerKit
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
async def cpu_action(game_id: str):
    """Execute CPU player's action."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
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
    
    # CPU decides action using PokerKit equity
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
    
    return game.get_state()


@router.post("/{game_id}/next-hand", response_model=GameState)
async def next_hand(game_id: str):
    """Start the next hand."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    game.next_hand()
    game.start_hand()
    
    return game.get_state()


@router.delete("/{game_id}")
async def delete_game(game_id: str):
    """End a game session."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    del games[game_id]
    return {"message": "Game deleted", "game_id": game_id}

