"""
CPU Player AI using equity calculations for decision making.

Player Types (2 dimensions):
- Aggression (0-1): Higher = more betting/raising, more bluffs
- Tightness (0-1): Higher = plays fewer hands, needs better equity to continue

Combinations:
- Loose-Aggressive (LAG): Low tightness, high aggression
- Tight-Aggressive (TAG): High tightness, high aggression  
- Loose-Passive (Calling Station): Low tightness, low aggression
- Tight-Passive (Rock/Nit): High tightness, low aggression
"""

import random
from typing import List, Tuple, Optional
from .ev_evaluator import EVEvaluator


class CPUPlayer:
    """
    AI player that makes decisions based on equity calculations.
    """
    
    @staticmethod
    def decide_action(
        hole_cards: List[str],
        community_cards: List[str],
        pot: int,
        current_bet: int,
        player_bet: int,
        player_chips: int,
        num_opponents: int,
        phase: str,
        available_actions: List[str],
        min_raise: int,
        aggression: float = 0.5,
        tightness: float = 0.5,
    ) -> Tuple[str, Optional[int]]:
        """
        Decide what action to take based on equity, aggression, and tightness.
        
        Aggression affects: bet sizing, raise frequency, bluff frequency
        Tightness affects: equity thresholds to call/bet, hand requirements
        """
        bet_to_call = current_bet - player_bet
        
        # Calculate equity (fewer iterations for speed)
        equity = EVEvaluator.calculate_equity(
            hole_cards,
            community_cards,
            num_opponents,
            iterations=1000
        )
        
        pot_odds = EVEvaluator.calculate_pot_odds(bet_to_call, pot)
        
        # Add randomness for variety
        equity_adjusted = equity + (random.random() - 0.5) * 0.15
        equity_adjusted = max(0, min(1, equity_adjusted))
        
        # Tightness affects equity thresholds
        # Tight players (0.75) need ~10% more equity to continue
        # Loose players (0.25) need ~10% less equity to continue
        tightness_modifier = (tightness - 0.5) * 0.2  # Range: -0.1 to +0.1
        
        # No bet to call (can check or bet)
        if bet_to_call == 0:
            # Threshold to bet for value
            # Base: 55%, Aggressive lowers it, Tight raises it
            bet_threshold = 0.55 - (aggression * 0.1) + tightness_modifier
            
            if equity_adjusted >= bet_threshold:
                if "bet" in available_actions:
                    bet_size = int(pot * (0.4 + aggression * 0.4))
                    bet_size = max(min_raise, min(bet_size, player_chips))
                    return "bet", bet_size
                elif "raise" in available_actions:
                    raise_size = int(pot * (0.4 + aggression * 0.4))
                    raise_size = max(min_raise, min(raise_size, player_chips))
                    return "raise", raise_size
            
            if "check" in available_actions:
                return "check", None
        
        # There's a bet to call
        else:
            # Tight players require more equity margin to raise
            raise_margin = 0.15 + (aggression * 0.1) + (tightness * 0.05)
            
            # Strong hand - consider raising
            if equity_adjusted >= pot_odds + raise_margin:
                # Raise frequency affected by aggression
                if "raise" in available_actions and random.random() < (0.25 + aggression * 0.35):
                    raise_size = int((pot + bet_to_call) * (0.5 + aggression * 0.3))
                    raise_size = max(min_raise, min(raise_size, player_chips))
                    return "raise", raise_size
            
            # Call threshold affected by tightness
            # Tight players need equity to clearly beat pot odds
            # Loose players will call with worse odds
            call_margin = -0.05 + tightness_modifier  # Tight: needs equity >= pot_odds + 0.05
            
            if equity_adjusted >= pot_odds + call_margin:
                if "call" in available_actions:
                    return "call", bet_to_call
            
            # Bluff (more likely with high aggression, less likely when tight)
            bluff_chance = aggression * 0.2 * (1 - tightness * 0.5)  # Tight players bluff less
            if random.random() < bluff_chance:
                if "raise" in available_actions:
                    raise_size = max(min_raise, int(pot * 0.4))
                    raise_size = min(raise_size, player_chips)
                    return "raise", raise_size
            
            if "fold" in available_actions:
                return "fold", None
        
        if "check" in available_actions:
            return "check", None
        return "fold", None

