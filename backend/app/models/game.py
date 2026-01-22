from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal


ActionType = Literal["fold", "check", "call", "bet", "raise"]
Phase = Literal["waiting", "preflop", "flop", "turn", "river", "showdown"]
AggressionLevel = Literal["passive", "medium", "aggressive", "random"]
TightnessLevel = Literal["loose", "medium", "tight", "random"]


class Card(BaseModel):
    suit: str  # "h", "d", "c", "s"
    rank: str  # "2"-"9", "T", "J", "Q", "K", "A"
    code: str  # "As", "Kh", "2c" etc.


class Player(BaseModel):
    id: str
    name: str
    chips: int
    hole_cards: Optional[List[Card]] = None  # None = hidden
    is_human: bool
    is_active: bool  # Still in current hand
    is_all_in: bool
    current_bet: int
    position: int
    is_folded: bool
    aggression: Optional[float] = None  # CPU aggression level (0-1), higher = more bets/raises
    tightness: Optional[float] = None  # CPU tightness level (0-1), higher = fewer hands played


class GameSettings(BaseModel):
    starting_chips: int = 1000
    small_blind: int = 10
    big_blind: int = 20
    num_opponents: int = 5
    aggression_level: AggressionLevel = "medium"
    tightness_level: TightnessLevel = "medium"
    
    @field_validator('big_blind')
    @classmethod
    def validate_big_blind(cls, v, info):
        data = info.data
        small_blind = data.get('small_blind', 10)
        starting_chips = data.get('starting_chips', 1000)
        
        # Big blind should be 2x small blind
        if v != small_blind * 2:
            raise ValueError('Big blind must be exactly 2x small blind')
        
        # Blinds shouldn't exceed 50% of starting chips
        if v > starting_chips * 0.5:
            raise ValueError('Big blind cannot exceed 50% of starting chips')
        
        return v
    
    @field_validator('small_blind')
    @classmethod
    def validate_small_blind(cls, v, info):
        data = info.data
        starting_chips = data.get('starting_chips', 1000)
        
        # Small blind shouldn't exceed 25% of starting chips
        if v > starting_chips * 0.25:
            raise ValueError('Small blind cannot exceed 25% of starting chips')
        
        if v < 1:
            raise ValueError('Small blind must be at least 1')
        
        return v


class GameState(BaseModel):
    id: str
    players: List[Player]
    community_cards: List[Card]
    pot: int
    current_bet: int
    dealer_position: int
    current_player: int
    phase: Phase
    small_blind: int
    big_blind: int
    available_actions: List[ActionType]
    min_raise: int
    max_raise: int


class EVResult(BaseModel):
    user_action: str
    optimal_action: str
    was_correct: bool
    equity: Optional[float] = None
    pot_odds: Optional[float] = None
    explanation: Optional[str] = None


class ActionRequest(BaseModel):
    action: ActionType
    amount: Optional[int] = None


class ActionResponse(BaseModel):
    success: bool
    ev_result: Optional[EVResult] = None
    game_state: GameState
    hand_complete: bool = False
    winner_id: Optional[str] = None

