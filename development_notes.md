# Development Notes

Technical implementation details and architecture decisions for the Poker EV Trainer.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ StartScreen │  │SettingsScreen│ │     GameScreen      │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
│                           │                    │             │
│                    localStorage          ┌─────┴─────┐       │
│                                          │           │       │
│                                    PokerTable  ActionPanel   │
│                                          │           │       │
│                                          │           │       │
│                                    PlayerSeat FeedbackOverlay│
│                                          │           │       │
└──────────────────────────────────────────┼───────────────────┘
                                         REST API
┌──────────────────────────────────────────┼───────────────────┐
│                        Backend (FastAPI)                     │
│  ┌─────────────────────────────────────────────────────────┐ ││  │                    routes/game.py                       │ │
│  │   POST /game/new  GET /game/{id}  POST /game/{id}/action│ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐                │
│         │                 │                 │                │
│  ┌──────┴──────┐  ┌───────┴───────┐  ┌──────┴──────┐         │
│  │ poker_game  │  │ ev_evaluator  │  │ cpu_player  │         │
│  │             │  │               │  │             │         │
│  │ Game state  │  │ Monte Carlo   │  │ AI decision │         │
│  │ management  │  │ equity calc   │  │ logic       │         │
│  └─────────────┘  └───────────────┘  └─────────────┘         │
└──────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Custom Hand Evaluator

Implemented a custom `HandEvaluator` class instead of using an external library (PokerKit) for:
- Simpler integration with our game state
- Full control over evaluation logic
- Easier debugging and testing

The evaluator checks all 5-card combinations from 7 cards (2 hole + 5 board) and returns the best hand.

### 2. Monte Carlo Equity Calculation

```python
def calculate_equity(hole_cards, community_cards, num_opponents, iterations=3000):
    # 1. Build deck excluding known cards
    # 2. For each iteration:
    #    - Shuffle remaining deck
    #    - Deal remaining community cards
    #    - Deal opponent hands
    #    - Compare hand strengths
    # 3. Return (wins + ties*0.5) / total
```

**Iteration counts:**
- User action evaluation: 2000 iterations (balance speed/accuracy)
- CPU decisions: 1000 iterations (faster, less critical)

### 3. Two-Dimensional CPU Personality

CPU players have independent **Aggression** and **Tightness** values (0.0 to 1.0):

```python
# Sampled from normal distribution based on settings
aggression = random.gauss(median, 0.1)  # median: 0.25/0.50/0.75
tightness = random.gauss(median, 0.1)
```

**How they affect decisions:**

| Trait | Affects |
|-------|---------|
| Aggression | Bet size (40-80% pot), raise frequency, bluff rate |
| Tightness | Equity threshold to call (+/- 10%), bluff suppression |

**Bluff calculation:**
```python
bluff_chance = aggression * 0.2 * (1 - tightness * 0.5)
```

### 4. Game State Management

The `PokerGame` class maintains:
- Player list with chips, cards, bets, status
- Community cards
- Pot size
- Current bet level
- Dealer position
- Game phase

**State is stored in-memory** (dict keyed by game_id). No database needed for single-session games.

### 5. Action Validation

Available actions are calculated based on:
- Current bet vs player's bet
- Player's chip stack
- Game phase

```python
def _get_available_actions(self):
    actions = ["fold"]
    if current_bet == player_bet:
        actions.append("check")
        if player_chips > 0:
            actions.append("bet")
    else:
        actions.append("call")
        if player_chips > call_amount:
            actions.append("raise")
    return actions
```

### 6. All-In Handling

When all active players are all-in:
1. `run_out_board()` deals remaining community cards
2. Game transitions to showdown
3. Winner determined by hand comparison
4. Pot awarded

### 7. Player Elimination

Players with 0 chips are marked `is_active = False` and:
- Skipped during blind posting
- Skipped during action
- Displayed greyed out with "OUT" badge

## Frontend State Flow

```
Settings (localStorage) ──┐
                          │
User clicks PLAY ─────────┼──> POST /game/new
                          │           │
                          │           v
                          │    GameState stored in
                          │    React useState
                          │           │
                          v           v
               ┌──────────────────────────────────┐
               │          Game Loop               │
               │                                  │
               │  Is current player human?        │
               │     YES ──> Show ActionPanel     │
               │             Wait for input       │
               │             POST /action         │
               │             Show feedback        │
               │                                  │
               │     NO ──> POST /cpu-action      │
               │            Update state          │
               │            Loop                  │
               │                                  │
               │  Is hand complete?               │
               │     YES ──> Show cards 10s       │
               │             POST /next-hand      │
               │                                  │
               └──────────────────────────────────┘
```

## EV Evaluation Logic

### Optimal Action Decision Tree

```
No bet to call?
├── Equity ≥ 65% ──> BET (66% pot)
├── Equity ≥ 45% ──> CHECK
└── Equity < 45% ──> CHECK

Bet to call?
├── Equity ≥ pot_odds + 20%
│   └── Equity ≥ 70% ──> RAISE (pot-sized)
│   └── Equity < 70% ──> RAISE (66% pot) or CALL
├── Equity ≥ pot_odds ──> CALL
└── Equity < pot_odds ──> FOLD
```

### "Correct" Action Tolerance

User action is marked correct if:
- Exact match with optimal
- Call when raise was optimal (still +EV)
- Bet/raise with 40%+ equity when check was optimal (acceptable aggression)

## Card Notation

**Internal format:** `{rank}{suit}` where:
- Rank: `2-9`, `T`, `J`, `Q`, `K`, `A`
- Suit: `h` (hearts), `d` (diamonds), `c` (clubs), `s` (spades)

**Examples:** `As` (Ace of spades), `Th` (Ten of hearts), `2c` (Two of clubs)

## API Response Transformation

Backend uses `snake_case`, frontend uses `camelCase`:

```typescript
// api.ts transforms responses
function transformGameState(data: any): GameState {
  return {
    currentBet: data.current_bet,
    dealerPosition: data.dealer_position,
    // ...
  }
}
```

## Performance Considerations

1. **Equity calculation** is the bottleneck (~100ms for 2000 iterations)
2. **CPU actions** use fewer iterations (1000) for faster play
3. **React StrictMode** causes double-mounting; prevented with `useRef`
4. **Game state polling** not needed; state updates on action responses

## Known Limitations

1. No side pot handling (simplified all-in)
2. No hand history tracking
3. No statistics/session tracking
4. Single game at a time (in-memory storage)
5. No authentication/persistence
