"""
EV Evaluator using Monte Carlo simulation for equity calculations.
"""

from typing import List, Tuple, Optional, Literal
import random
from itertools import combinations

ActionType = Literal["fold", "check", "call", "bet", "raise"]

# Hand rankings
HAND_RANKS = {
    'high_card': 0,
    'pair': 1,
    'two_pair': 2,
    'three_kind': 3,
    'straight': 4,
    'flush': 5,
    'full_house': 6,
    'four_kind': 7,
    'straight_flush': 8,
    'royal_flush': 9,
}

RANK_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
               '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}


class HandEvaluator:
    """Simple hand evaluator for Texas Hold'em."""
    
    @staticmethod
    def evaluate(hole_cards: List[str], board: List[str]) -> Tuple[int, List[int]]:
        """
        Evaluate a poker hand.
        Returns (hand_rank, kickers) where higher is better.
        """
        all_cards = hole_cards + board
        
        if len(all_cards) < 5:
            # Not enough cards, return high card
            ranks = sorted([RANK_VALUES[c[0]] for c in all_cards], reverse=True)
            return (HAND_RANKS['high_card'], ranks[:5])
        
        # Get all 5-card combinations and find best hand
        best_hand = (0, [0])
        
        for combo in combinations(all_cards, 5):
            hand_value = HandEvaluator._evaluate_five(list(combo))
            if hand_value > best_hand:
                best_hand = hand_value
        
        return best_hand
    
    @staticmethod
    def _evaluate_five(cards: List[str]) -> Tuple[int, List[int]]:
        """Evaluate exactly 5 cards."""
        ranks = sorted([RANK_VALUES[c[0]] for c in cards], reverse=True)
        suits = [c[1] for c in cards]
        
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight = False
        straight_high = 0
        
        unique_ranks = sorted(set(ranks), reverse=True)
        if len(unique_ranks) >= 5:
            for i in range(len(unique_ranks) - 4):
                if unique_ranks[i] - unique_ranks[i+4] == 4:
                    is_straight = True
                    straight_high = unique_ranks[i]
                    break
        
        # Check for A-2-3-4-5 straight (wheel)
        if set(ranks) == {14, 2, 3, 4, 5}:
            is_straight = True
            straight_high = 5  # 5-high straight
        
        # Count rank occurrences
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        
        counts = sorted(rank_counts.values(), reverse=True)
        sorted_by_count = sorted(rank_counts.keys(), key=lambda x: (rank_counts[x], x), reverse=True)
        
        # Determine hand type
        if is_straight and is_flush:
            if straight_high == 14:
                return (HAND_RANKS['royal_flush'], [14])
            return (HAND_RANKS['straight_flush'], [straight_high])
        
        if counts == [4, 1]:
            return (HAND_RANKS['four_kind'], sorted_by_count)
        
        if counts == [3, 2]:
            return (HAND_RANKS['full_house'], sorted_by_count)
        
        if is_flush:
            return (HAND_RANKS['flush'], ranks)
        
        if is_straight:
            return (HAND_RANKS['straight'], [straight_high])
        
        if counts == [3, 1, 1]:
            return (HAND_RANKS['three_kind'], sorted_by_count)
        
        if counts == [2, 2, 1]:
            return (HAND_RANKS['two_pair'], sorted_by_count)
        
        if counts == [2, 1, 1, 1]:
            return (HAND_RANKS['pair'], sorted_by_count)
        
        return (HAND_RANKS['high_card'], ranks)


class EVEvaluator:
    """
    Evaluates poker decisions using Monte Carlo simulation for equity calculations.
    """
    
    @staticmethod
    def calculate_equity(
        hole_cards: List[str],
        community_cards: List[str],
        num_opponents: int = 1,
        iterations: int = 3000
    ) -> float:
        """
        Calculate hand equity using Monte Carlo simulation.
        """
        if not hole_cards or len(hole_cards) < 2:
            return 0.0
        
        if num_opponents <= 0:
            return 1.0
            
        # Build deck excluding known cards
        all_ranks = '23456789TJQKA'
        all_suits = 'shdc'
        
        known_cards = set(hole_cards + community_cards)
        deck = [
            r + s for r in all_ranks for s in all_suits
            if (r + s) not in known_cards
        ]
        
        wins = 0
        ties = 0
        total = 0
        
        for _ in range(iterations):
            random.shuffle(deck)
            deck_idx = 0
            
            # Deal remaining community cards
            remaining_community = 5 - len(community_cards)
            simulated_board = list(community_cards)
            for _ in range(remaining_community):
                simulated_board.append(deck[deck_idx])
                deck_idx += 1
            
            # Deal opponent hands
            opponent_hands = []
            for _ in range(num_opponents):
                opp_hand = [deck[deck_idx], deck[deck_idx + 1]]
                deck_idx += 2
                opponent_hands.append(opp_hand)
            
            # Evaluate player's hand
            player_value = HandEvaluator.evaluate(hole_cards, simulated_board)
            
            # Evaluate opponent hands and find best
            best_opponent_value = (-1, [0])
            for opp_hand in opponent_hands:
                opp_value = HandEvaluator.evaluate(opp_hand, simulated_board)
                if opp_value > best_opponent_value:
                    best_opponent_value = opp_value
            
            # Compare
            if player_value > best_opponent_value:
                wins += 1
            elif player_value == best_opponent_value:
                ties += 1
            
            total += 1
        
        if total == 0:
            return 0.5
            
        return (wins + ties * 0.5) / total
    
    @staticmethod
    def calculate_pot_odds(bet_to_call: int, pot_size: int) -> float:
        """Calculate pot odds (equity needed to break even)."""
        if bet_to_call <= 0:
            return 0.0
        return bet_to_call / (pot_size + bet_to_call)
    
    @staticmethod
    def get_optimal_action(
        hole_cards: List[str],
        community_cards: List[str],
        pot: int,
        current_bet: int,
        player_bet: int,
        player_chips: int,
        num_opponents: int,
        phase: str,
        available_actions: List[ActionType],
        min_raise: int,
        equity: Optional[float] = None,
    ) -> Tuple[ActionType, Optional[int], str, float, float]:
        """
        Determine the optimal action based on equity and pot odds.
        """
        bet_to_call = current_bet - player_bet
        pot_odds = EVEvaluator.calculate_pot_odds(bet_to_call, pot)
        
        # Calculate equity
        equity = EVEvaluator.calculate_equity(
            hole_cards, 
            community_cards, 
            num_opponents,
            iterations=2000
        )
        
        explanation = ""
        
        # No bet to call
        if bet_to_call == 0:
            if equity >= 0.65:
                # Strong hand - bet/raise for value
                if "bet" in available_actions:
                    bet_size = max(min_raise, int(pot * 0.66))
                    bet_size = min(bet_size, player_chips)
                    explanation = f"Strong equity ({equity:.0%}) - bet for value"
                    return "bet", bet_size, explanation
                elif "raise" in available_actions:
                    raise_size = max(min_raise, int(pot * 0.66))
                    raise_size = min(raise_size, player_chips)
                    explanation = f"Strong equity ({equity:.0%}) - raise for value"
                    return "raise", raise_size, explanation
            
            if equity >= 0.45:
                explanation = f"Medium equity ({equity:.0%}) - check"
                return "check", None, explanation
            
            explanation = f"Weak equity ({equity:.0%}) - check"
            return "check", None, explanation
        
        # There's a bet to call
        else:
            # Strong equity - raise for value
            if equity >= pot_odds + 0.20:
                if "raise" in available_actions:
                    if equity >= 0.70:
                        raise_size = pot + bet_to_call
                    else:
                        raise_size = int((pot + bet_to_call) * 0.66)
                    raise_size = max(min_raise, min(raise_size, player_chips))
                    explanation = f"Strong equity ({equity:.0%}) vs pot odds ({pot_odds:.0%}) - raise for value"
                    return "raise", raise_size, explanation
                elif "call" in available_actions:
                    explanation = f"Strong equity ({equity:.0%}) - call is profitable"
                    return "call", bet_to_call, explanation
            
            # Equity beats pot odds - call
            if equity >= pot_odds:
                if "call" in available_actions:
                    explanation = f"Equity ({equity:.0%}) exceeds pot odds ({pot_odds:.0%}) - call"
                    return "call", bet_to_call, explanation
            
            # Fold
            explanation = f"Equity ({equity:.0%}) below pot odds ({pot_odds:.0%}) - fold"
            return "fold", None, explanation
        
        # Fallback
        if "check" in available_actions:
            return "check", None, "Default: check"
        return "fold", None, "Default: fold"
    
    @staticmethod
    def evaluate_user_action(
        user_action: ActionType,
        user_amount: Optional[int],
        hole_cards: List[str],
        community_cards: List[str],
        pot: int,
        current_bet: int,
        player_bet: int,
        player_chips: int,
        num_opponents: int,
        phase: str,
        available_actions: List[ActionType],
        min_raise: int,
        cached_equity: Optional[float] = None,
    ) -> dict:
        """Evaluate if the user's action was optimal."""
        # Use cached equity if available, otherwise calculate
        if cached_equity is not None:
            equity = cached_equity
        else:
            equity = EVEvaluator.calculate_equity(
                hole_cards, 
                community_cards, 
                num_opponents,
                iterations=2000
            )
        
        bet_to_call = current_bet - player_bet
        pot_odds = EVEvaluator.calculate_pot_odds(bet_to_call, pot)
        
        # Determine optimal action based on the calculated equity
        optimal_action, optimal_amount, explanation = EVEvaluator._get_optimal_action_with_equity(
            equity=equity,
            pot_odds=pot_odds,
            bet_to_call=bet_to_call,
            pot=pot,
            player_chips=player_chips,
            available_actions=available_actions,
            min_raise=min_raise,
        )
        
        # Check if user action matches optimal
        was_correct = False
        
        if user_action == optimal_action:
            was_correct = True
        elif user_action == "call" and optimal_action == "raise":
            was_correct = True  # Still +EV
            explanation += " (Call is also acceptable)"
        elif user_action in ["bet", "raise"] and optimal_action == "check" and equity >= 0.40:
            was_correct = True
            explanation = f"Aggressive play with {equity:.0%} equity is acceptable"
        
        return {
            "user_action": user_action,
            "optimal_action": optimal_action,
            "was_correct": was_correct,
            "equity": round(equity, 3),
            "pot_odds": round(pot_odds, 3) if bet_to_call > 0 else None,
            "explanation": explanation,
        }
    
    @staticmethod
    def _get_optimal_action_with_equity(
        equity: float,
        pot_odds: float,
        bet_to_call: int,
        pot: int,
        player_chips: int,
        available_actions: List[ActionType],
        min_raise: int,
    ) -> Tuple[ActionType, Optional[int], str]:
        """Determine optimal action given pre-calculated equity."""
        # No bet to call
        if bet_to_call == 0:
            if equity >= 0.65:
                if "bet" in available_actions:
                    bet_size = max(min_raise, int(pot * 0.66))
                    bet_size = min(bet_size, player_chips)
                    return "bet", bet_size, f"Strong equity ({equity:.0%}) - bet for value"
                elif "raise" in available_actions:
                    raise_size = max(min_raise, int(pot * 0.66))
                    raise_size = min(raise_size, player_chips)
                    return "raise", raise_size, f"Strong equity ({equity:.0%}) - raise for value"
            
            if equity >= 0.45:
                return "check", None, f"Medium equity ({equity:.0%}) - check"
            
            return "check", None, f"Weak equity ({equity:.0%}) - check"
        
        # There's a bet to call
        else:
            if equity >= pot_odds + 0.20:
                if "raise" in available_actions:
                    if equity >= 0.70:
                        raise_size = pot + bet_to_call
                    else:
                        raise_size = int((pot + bet_to_call) * 0.66)
                    raise_size = max(min_raise, min(raise_size, player_chips))
                    return "raise", raise_size, f"Strong equity ({equity:.0%}) vs pot odds ({pot_odds:.0%}) - raise for value"
                elif "call" in available_actions:
                    return "call", bet_to_call, f"Strong equity ({equity:.0%}) - call is profitable"
            
            if equity >= pot_odds:
                if "call" in available_actions:
                    return "call", bet_to_call, f"Equity ({equity:.0%}) exceeds pot odds ({pot_odds:.0%}) - call"
            
            return "fold", None, f"Equity ({equity:.0%}) below pot odds ({pot_odds:.0%}) - fold"
        
        if "check" in available_actions:
            return "check", None, "Default: check"
        return "fold", None, "Default: fold"
