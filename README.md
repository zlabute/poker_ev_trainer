# Poker EV Trainer

A full-stack web application for training poker decision-making through Expected Value (EV) analysis. Play No-Limit Texas Hold'em against CPU opponents and receive real-time feedback on whether your decisions are mathematically optimal.

![Poker EV Trainer](https://img.shields.io/badge/React-18-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green) ![Python](https://img.shields.io/badge/Python-3.11+-yellow)

## Features

- **Real-time EV Feedback**: After each decision, see whether your play was correct based on equity and pot odds
- **Monte Carlo Equity Calculation**: Accurate equity calculations using thousands of simulated outcomes
- **Configurable CPU Opponents**: 
  - **Aggression Level** (Passive → Aggressive): Controls bet sizing, raise frequency, and bluff frequency
  - **Tightness Level** (Loose → Tight): Controls hand selection and calling thresholds
- **Complete Texas Hold'em**: All betting rounds (pre-flop, flop, turn, river) with proper blind structure
- **Visual Feedback**: Green/red overlays showing equity, pot odds, and explanations
- **Player Elimination**: Players who lose all chips are marked "OUT" and skipped
- **Showdown Display**: Cards revealed at showdown for all active players

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, CSS Modules |
| **Backend** | Python 3.11+, FastAPI, Pydantic |
| **Poker Logic** | Custom hand evaluator with Monte Carlo simulations |

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd poker_ev_trainer
   ```

2. **Set up the backend**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start the backend** (from project root)
   ```bash
   source venv/bin/activate
   cd backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser** to `http://localhost:5173`

## How It Works

### Equity Calculation

The app uses Monte Carlo simulation to calculate your hand's equity:

1. Takes your hole cards and current community cards
2. Simulates remaining community cards (if any)
3. Deals random hands to opponents
4. Compares hand strengths across thousands of iterations
5. Returns win probability as a percentage

**Example**: With A♠K♠ on a flop of Q♠J♠2♥, equity might be ~55% (flush draw + overcards).

### EV Decision Logic

After each action, the app evaluates whether you made the optimal play:

| Situation | Optimal Action |
|-----------|----------------|
| Equity ≥ 65%, no bet | Bet for value |
| Equity 45-65%, no bet | Check |
| Equity ≥ pot odds + 20% | Raise |
| Equity ≥ pot odds | Call |
| Equity < pot odds | Fold |

### CPU Player Behavior

CPU players have two independent personality traits:

**Aggression (A)** - Higher = more bets/raises/bluffs
- Affects bet sizing (40-80% pot)
- Affects raise frequency
- Affects bluff frequency

**Tightness (T)** - Higher = plays fewer hands
- Raises equity threshold to bet/call
- Reduces bluff frequency
- More selective hand requirements

This creates 4 classic player types:
| Type | Aggression | Tightness |
|------|------------|-----------|
| LAG (Loose-Aggressive) | High | Low |
| TAG (Tight-Aggressive) | High | High |
| Calling Station | Low | Low |
| Rock/Nit | Low | High |

## Configuration

### Game Settings

Access settings from the start screen:

| Setting | Default | Description |
|---------|---------|-------------|
| Starting Chips | 1000 | Each player's initial stack |
| Small Blind | 10 | Posted by player left of dealer |
| Big Blind | 20 | Must be 2x small blind |
| Opponents | 5 | Number of CPU players (1-8) |
| Aggression Level | Medium | CPU aggression distribution |
| Tightness Level | Medium | CPU tightness distribution |
| Show Aggression | On | Display A% on player seats |
| Show Tightness | On | Display T% on player seats |

**Validation**: Big blind cannot exceed 50% of starting chips.

## Project Structure

```
poker_ev_trainer/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ActionPanel.tsx      # Fold/Check/Call/Bet/Raise buttons
│   │   │   ├── Card.tsx             # Playing card display
│   │   │   ├── FeedbackOverlay.tsx  # EV result popup
│   │   │   ├── PlayerSeat.tsx       # Player info, cards, stats
│   │   │   └── PokerTable.tsx       # Table layout with seats
│   │   ├── screens/
│   │   │   ├── GameScreen.tsx       # Main game interface
│   │   │   ├── SettingsScreen.tsx   # Game configuration
│   │   │   └── StartScreen.tsx      # Landing page
│   │   ├── services/
│   │   │   └── api.ts               # Backend API calls
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript interfaces
│   │   └── styles/
│   │       └── global.css           # CSS variables, base styles
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── game.py              # Pydantic models
│   │   ├── services/
│   │   │   ├── cpu_player.py        # CPU decision AI
│   │   │   ├── ev_evaluator.py      # Equity & optimal action
│   │   │   └── poker_game.py        # Game state management
│   │   ├── routes/
│   │   │   └── game.py              # API endpoints
│   │   └── main.py                  # FastAPI app
│   └── requirements.txt
├── venv/                            # Python virtual environment
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/game/new` | Create new game with settings |
| GET | `/api/game/{id}` | Get current game state |
| POST | `/api/game/{id}/action` | Submit player action |
| POST | `/api/game/{id}/cpu-action` | Execute next CPU action |
| POST | `/api/game/{id}/next-hand` | Start the next hand |
| DELETE | `/api/game/{id}` | End game session |

### Example: Submit Action

**Request:**
```json
POST /api/game/{id}/action
{
  "action": "raise",
  "amount": 60
}
```

**Response:**
```json
{
  "success": true,
  "ev_result": {
    "user_action": "raise",
    "optimal_action": "raise", 
    "was_correct": true,
    "equity": 0.72,
    "pot_odds": 0.25,
    "explanation": "Strong equity (72%) vs pot odds (25%) - raise for value"
  },
  "game_state": { ... },
  "hand_complete": false,
  "winner_id": null
}
```

## Texas Hold'em Rules Reference

### Hand Rankings (Highest to Lowest)
1. Royal Flush - A, K, Q, J, 10 same suit
2. Straight Flush - Five consecutive, same suit
3. Four of a Kind - Four cards same rank
4. Full House - Three of a kind + pair
5. Flush - Five cards same suit
6. Straight - Five consecutive cards
7. Three of a Kind - Three cards same rank
8. Two Pair - Two different pairs
9. One Pair - Two cards same rank
10. High Card - Highest card wins

### Betting Actions
| Action | When Available |
|--------|----------------|
| Fold | Always |
| Check | No bet to call |
| Call | Bet exists |
| Bet | No bet exists |
| Raise | Bet exists |

### Game Flow
1. **Pre-flop**: 2 hole cards dealt, betting starts left of big blind
2. **Flop**: 3 community cards, betting starts left of dealer
3. **Turn**: 4th community card, betting round
4. **River**: 5th community card, final betting
5. **Showdown**: Best 5-card hand wins

## Development

### Running Tests
```bash
cd backend
python -m pytest tests/
```

### Code Style
- Frontend: ESLint + Prettier
- Backend: Black + isort

## License

MIT License - feel free to use for learning and personal projects.

