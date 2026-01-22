"""
Poker game management using PokerKit.
"""

import uuid
import random
from typing import List, Optional, Dict, Any
from ..models.game import Card, Player, GameState, GameSettings, ActionType


class PokerGame:
    """
    Manages a poker game session.
    """
    
    RANKS = "23456789TJQKA"
    SUITS = "shdc"
    SUIT_NAMES = {"s": "spades", "h": "hearts", "d": "diamonds", "c": "clubs"}
    
    def __init__(self, settings: GameSettings):
        self.id = str(uuid.uuid4())
        self.settings = settings
        self.num_players = settings.num_opponents + 1
        self.small_blind = settings.small_blind
        self.big_blind = settings.big_blind
        
        # Initialize players
        self.players: List[Dict[str, Any]] = []
        self._init_players()
        
        # Game state
        self.deck: List[str] = []
        self.community_cards: List[str] = []
        self.pot = 0
        self.current_bet = 0
        self.dealer_position = 0
        self.current_player = 0
        self.phase = "waiting"
        self.betting_round_complete = False
        self.last_raiser: Optional[int] = None
        self.players_acted_this_round: set = set()
    
    def _sample_aggression(self) -> float:
        """Sample aggression level based on settings."""
        level = self.settings.aggression_level
        
        if level == "passive":
            # Normal distribution centered at 0.25
            aggression = random.gauss(0.25, 0.1)
        elif level == "medium":
            # Normal distribution centered at 0.50
            aggression = random.gauss(0.50, 0.1)
        elif level == "aggressive":
            # Normal distribution centered at 0.75
            aggression = random.gauss(0.75, 0.1)
        else:  # random
            aggression = random.random()
        
        # Clamp between 0.05 and 0.95
        return max(0.05, min(0.95, aggression))
    
    def _sample_tightness(self) -> float:
        """Sample tightness level based on settings."""
        level = self.settings.tightness_level
        
        if level == "loose":
            # Normal distribution centered at 0.25 (plays many hands)
            tightness = random.gauss(0.25, 0.1)
        elif level == "medium":
            # Normal distribution centered at 0.50
            tightness = random.gauss(0.50, 0.1)
        elif level == "tight":
            # Normal distribution centered at 0.75 (plays few hands)
            tightness = random.gauss(0.75, 0.1)
        else:  # random
            tightness = random.random()
        
        # Clamp between 0.05 and 0.95
        return max(0.05, min(0.95, tightness))
        
    def _init_players(self):
        """Initialize all players."""
        # Human player at position 0
        self.players.append({
            "id": "human",
            "name": "YOU",
            "chips": self.settings.starting_chips,
            "hole_cards": [],
            "is_human": True,
            "is_active": True,
            "is_all_in": False,
            "current_bet": 0,
            "position": 0,
            "is_folded": False,
            "aggression": 0.5,  # Not used for human
            "tightness": 0.5,  # Not used for human
        })
        
        # CPU players - each gets their own aggression and tightness levels
        for i in range(1, self.num_players):
            self.players.append({
                "id": f"cpu-{i}",
                "name": f"CPU {i}",
                "chips": self.settings.starting_chips,
                "hole_cards": [],
                "is_human": False,
                "is_active": True,
                "is_all_in": False,
                "current_bet": 0,
                "position": i,
                "is_folded": False,
                "aggression": self._sample_aggression(),
                "tightness": self._sample_tightness(),
            })
    
    def _create_deck(self) -> List[str]:
        """Create and shuffle a new deck."""
        deck = [r + s for r in self.RANKS for s in self.SUITS]
        random.shuffle(deck)
        return deck
    
    def _card_to_model(self, card_code: str) -> Card:
        """Convert card code to Card model."""
        return Card(
            suit=card_code[1],
            rank=card_code[0],
            code=card_code
        )
    
    def start_hand(self):
        """Start a new hand."""
        # Reset state
        self.deck = self._create_deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.phase = "preflop"
        self.last_raiser = None
        self.players_acted_this_round = set()
        
        # Reset player states - players with 0 chips are OUT
        for player in self.players:
            player["hole_cards"] = []
            player["current_bet"] = 0
            player["is_folded"] = False
            player["is_all_in"] = False
            player["is_active"] = player["chips"] > 0
        
        # Check if we have enough active players
        active_players = [p for p in self.players if p["is_active"]]
        if len(active_players) < 2:
            self.phase = "waiting"
            return
        
        # Deal hole cards only to active players
        for player in self.players:
            if player["is_active"]:
                player["hole_cards"] = [self.deck.pop(), self.deck.pop()]
        
        # Find small blind position (skip eliminated players)
        sb_pos = self._find_next_active_position(self.dealer_position)
        # Find big blind position (skip eliminated players)
        bb_pos = self._find_next_active_position(sb_pos)
        
        # Post small blind
        sb_amount = min(self.small_blind, self.players[sb_pos]["chips"])
        self.players[sb_pos]["chips"] -= sb_amount
        self.players[sb_pos]["current_bet"] = sb_amount
        self.pot += sb_amount
        if self.players[sb_pos]["chips"] == 0:
            self.players[sb_pos]["is_all_in"] = True
        
        # Post big blind
        bb_amount = min(self.big_blind, self.players[bb_pos]["chips"])
        self.players[bb_pos]["chips"] -= bb_amount
        self.players[bb_pos]["current_bet"] = bb_amount
        self.pot += bb_amount
        self.current_bet = bb_amount
        if self.players[bb_pos]["chips"] == 0:
            self.players[bb_pos]["is_all_in"] = True
        
        # Action starts left of big blind (skip eliminated players)
        self.current_player = self._find_next_active_position(bb_pos)
        self._skip_inactive_players()
    
    def _find_next_active_position(self, from_pos: int) -> int:
        """Find the next active player position after from_pos."""
        pos = (from_pos + 1) % self.num_players
        attempts = 0
        while attempts < self.num_players:
            if self.players[pos]["is_active"]:
                return pos
            pos = (pos + 1) % self.num_players
            attempts += 1
        return from_pos  # Fallback
    
    def _skip_inactive_players(self):
        """Move to next active player."""
        attempts = 0
        while attempts < self.num_players:
            player = self.players[self.current_player]
            if player["is_active"] and not player["is_folded"] and not player["is_all_in"]:
                return
            self.current_player = (self.current_player + 1) % self.num_players
            attempts += 1
    
    def _get_active_players(self) -> List[Dict]:
        """Get list of players still in hand."""
        return [p for p in self.players if p["is_active"] and not p["is_folded"]]
    
    def _get_available_actions(self) -> List[ActionType]:
        """Get available actions for current player."""
        player = self.players[self.current_player]
        actions: List[ActionType] = ["fold"]
        
        if self.current_bet == player["current_bet"]:
            actions.append("check")
        else:
            actions.append("call")
        
        # Can raise if not all-in and have chips
        if player["chips"] > (self.current_bet - player["current_bet"]):
            if self.current_bet == 0:
                actions.append("bet")
            else:
                actions.append("raise")
        
        return actions
    
    def apply_action(self, action: ActionType, amount: Optional[int] = None) -> bool:
        """
        Apply an action for the current player.
        Returns True if successful.
        """
        player = self.players[self.current_player]
        
        if action == "fold":
            player["is_folded"] = True
            
        elif action == "check":
            if self.current_bet > player["current_bet"]:
                return False  # Can't check with active bet
                
        elif action == "call":
            call_amount = self.current_bet - player["current_bet"]
            actual_call = min(call_amount, player["chips"])
            player["chips"] -= actual_call
            player["current_bet"] += actual_call
            self.pot += actual_call
            if player["chips"] == 0:
                player["is_all_in"] = True
                
        elif action in ["bet", "raise"]:
            if amount is None:
                amount = self.big_blind * 2
            
            # Ensure minimum raise
            min_raise = self.current_bet + self.big_blind
            amount = max(amount, min_raise)
            amount = min(amount, player["chips"] + player["current_bet"])
            
            bet_amount = amount - player["current_bet"]
            player["chips"] -= bet_amount
            self.pot += bet_amount
            player["current_bet"] = amount
            self.current_bet = amount
            self.last_raiser = self.current_player
            
            if player["chips"] == 0:
                player["is_all_in"] = True
        
        self.players_acted_this_round.add(self.current_player)
        
        # Move to next player
        self._advance_action()
        
        return True
    
    def _advance_action(self):
        """Advance to next player or next phase."""
        active = self._get_active_players()
        
        # Only one player left - hand is over
        if len(active) <= 1:
            self.phase = "showdown"
            return
        
        # Find next player who can act
        next_player = (self.current_player + 1) % self.num_players
        attempts = 0
        
        while attempts < self.num_players:
            p = self.players[next_player]
            
            # Skip folded, all-in, or inactive players
            if p["is_folded"] or p["is_all_in"] or not p["is_active"]:
                next_player = (next_player + 1) % self.num_players
                attempts += 1
                continue
            
            # Check if betting round is complete
            if self._is_betting_complete(next_player):
                self._advance_phase()
                return
            
            self.current_player = next_player
            return
        
        # All players are all-in or folded
        self._advance_phase()
    
    def _skip_to_next_player(self):
        """Skip to the next player who can act, or advance phase if needed."""
        next_player = (self.current_player + 1) % self.num_players
        attempts = 0
        
        while attempts < self.num_players:
            p = self.players[next_player]
            
            if not p["is_folded"] and not p["is_all_in"] and p["is_active"]:
                self.current_player = next_player
                return
            
            next_player = (next_player + 1) % self.num_players
            attempts += 1
        
        # No one can act - advance phase
        self._advance_phase()
    
    def _is_betting_complete(self, next_player: int) -> bool:
        """Check if current betting round is complete."""
        active = [p for p in self.players if p["is_active"] and not p["is_folded"] and not p["is_all_in"]]
        
        if len(active) == 0:
            return True
        
        # All active players must have matched the bet and had a chance to act
        for player in active:
            if player["current_bet"] < self.current_bet:
                return False
            if player["position"] not in self.players_acted_this_round:
                return False
        
        # If there was a raise, action must get back to raiser
        if self.last_raiser is not None:
            if next_player != self.last_raiser:
                # Check if all players between have acted
                return all(
                    p["position"] in self.players_acted_this_round or p["is_folded"] or p["is_all_in"]
                    for p in active
                )
        
        return True
    
    def _advance_phase(self):
        """Move to the next phase of the hand."""
        # Reset betting round
        for player in self.players:
            player["current_bet"] = 0
        self.current_bet = 0
        self.last_raiser = None
        self.players_acted_this_round = set()
        
        if self.phase == "preflop":
            self.phase = "flop"
            # Burn and deal 3
            self.deck.pop()
            self.community_cards = [self.deck.pop() for _ in range(3)]
            
        elif self.phase == "flop":
            self.phase = "turn"
            # Burn and deal 1
            self.deck.pop()
            self.community_cards.append(self.deck.pop())
            
        elif self.phase == "turn":
            self.phase = "river"
            # Burn and deal 1
            self.deck.pop()
            self.community_cards.append(self.deck.pop())
            
        elif self.phase == "river":
            self.phase = "showdown"
            return
        
        # Action starts left of dealer post-flop
        self.current_player = (self.dealer_position + 1) % self.num_players
        self._skip_inactive_players()
    
    def is_all_in_runout_needed(self) -> bool:
        """Check if all active players are all-in and we need to run out cards."""
        if self.phase == "showdown":
            return False
        
        active = self._get_active_players()
        
        if len(active) <= 1:
            return False
        
        # Check if all remaining active players are all-in
        players_who_can_act = [
            p for p in active 
            if not p["is_all_in"] and not p["is_folded"]
        ]
        
        return len(players_who_can_act) == 0
    
    def run_out_board(self):
        """Deal remaining community cards when all players are all-in."""
        while self.phase != "showdown":
            # Deal remaining cards
            if self.phase == "preflop":
                self.phase = "flop"
                self.deck.pop()  # Burn
                self.community_cards = [self.deck.pop() for _ in range(3)]
            elif self.phase == "flop":
                self.phase = "turn"
                self.deck.pop()  # Burn
                self.community_cards.append(self.deck.pop())
            elif self.phase == "turn":
                self.phase = "river"
                self.deck.pop()  # Burn
                self.community_cards.append(self.deck.pop())
            elif self.phase == "river":
                self.phase = "showdown"
                break
    
    def get_winner(self) -> Optional[str]:
        """Determine the winner of the hand."""
        from .ev_evaluator import HandEvaluator
        
        active = self._get_active_players()
        
        if len(active) == 1:
            return active[0]["id"]
        
        if len(active) == 0:
            return None
        
        # Evaluate hands
        best_player = None
        best_hand = None
        
        for player in active:
            hand = HandEvaluator.evaluate(
                player["hole_cards"],
                self.community_cards
            )
            if best_hand is None or hand > best_hand:
                best_hand = hand
                best_player = player
        
        return best_player["id"] if best_player else None
    
    def award_pot(self, winner_id: str):
        """Award the pot to the winner."""
        for player in self.players:
            if player["id"] == winner_id:
                player["chips"] += self.pot
                break
        self.pot = 0
    
    def next_hand(self):
        """Setup for the next hand."""
        self.dealer_position = (self.dealer_position + 1) % self.num_players
        
        # Remove eliminated players (chips = 0)
        # For now, just mark them as inactive
        for player in self.players:
            if player["chips"] <= 0:
                player["is_active"] = False
    
    def get_state(self, for_player_id: str = "human") -> GameState:
        """Get current game state, hiding opponent cards unless at showdown."""
        players = []
        
        for p in self.players:
            # Show hole cards for:
            # 1. The requesting player (human)
            # 2. All active (non-folded) players at showdown
            hole_cards = None
            if p["hole_cards"]:
                if p["id"] == for_player_id:
                    hole_cards = [self._card_to_model(c) for c in p["hole_cards"]]
                elif self.phase == "showdown" and not p["is_folded"] and p["is_active"]:
                    hole_cards = [self._card_to_model(c) for c in p["hole_cards"]]
            
            players.append(Player(
                id=p["id"],
                name=p["name"],
                chips=p["chips"],
                hole_cards=hole_cards,
                is_human=p["is_human"],
                is_active=p["is_active"],
                is_all_in=p["is_all_in"],
                current_bet=p["current_bet"],
                position=p["position"],
                is_folded=p["is_folded"],
                aggression=p.get("aggression") if not p["is_human"] else None,
                tightness=p.get("tightness") if not p["is_human"] else None,
            ))
        
        # Calculate min/max raise
        current_player = self.players[self.current_player]
        min_raise = self.current_bet + self.big_blind
        max_raise = current_player["chips"] + current_player["current_bet"]
        
        return GameState(
            id=self.id,
            players=players,
            community_cards=[self._card_to_model(c) for c in self.community_cards],
            pot=self.pot,
            current_bet=self.current_bet,
            dealer_position=self.dealer_position,
            current_player=self.current_player,
            phase=self.phase,
            small_blind=self.small_blind,
            big_blind=self.big_blind,
            available_actions=self._get_available_actions(),
            min_raise=min_raise,
            max_raise=max_raise,
        )
    
    def get_human_hole_cards(self) -> List[str]:
        """Get human player's hole cards."""
        for player in self.players:
            if player["is_human"]:
                return player["hole_cards"]
        return []
    
    def get_num_active_opponents(self) -> int:
        """Get number of opponents still in hand."""
        return len([
            p for p in self.players 
            if not p["is_human"] and not p["is_folded"] and p["is_active"]
        ])

