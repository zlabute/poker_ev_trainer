// Card representation
export interface Card {
  suit: 'h' | 'd' | 'c' | 's'
  rank: string // "2"-"9", "T", "J", "Q", "K", "A"
  code: string // "As", "Kh", "2c" etc.
}

// Player in the game
export interface Player {
  id: string
  name: string
  chips: number
  holeCards: Card[] | null // null = hidden (for opponents)
  isHuman: boolean
  isActive: boolean // Still in current hand
  isAllIn: boolean
  currentBet: number
  position: number // Seat position (0-8)
  isFolded: boolean
  aggression: number | null // CPU aggression level (0-1)
  tightness: number | null // CPU tightness level (0-1)
}

// Game state from backend
export interface GameState {
  id: string
  players: Player[]
  communityCards: Card[]
  pot: number
  currentBet: number
  dealerPosition: number
  currentPlayer: number
  phase: 'waiting' | 'preflop' | 'flop' | 'turn' | 'river' | 'showdown'
  smallBlind: number
  bigBlind: number
  availableActions: ActionType[]
  minRaise: number
  maxRaise: number
}

// EV evaluation result
export interface EVResult {
  userAction: string
  optimalAction: string
  wasCorrect: boolean
  equity: number | null
  potOdds: number | null
  explanation: string | null
}

// Player action types
export type ActionType = 'fold' | 'check' | 'call' | 'bet' | 'raise'

// Action request to backend
export interface ActionRequest {
  action: ActionType
  amount?: number
}

// Aggression level for CPU players
export type AggressionLevel = 'passive' | 'medium' | 'aggressive' | 'random'

// Tightness level for CPU players
export type TightnessLevel = 'loose' | 'medium' | 'tight' | 'random'

// Settings
export interface GameSettings {
  startingChips: number
  smallBlind: number
  bigBlind: number
  numOpponents: number
  aggressionLevel: AggressionLevel
  tightnessLevel: TightnessLevel
  showAggression: boolean
  showTightness: boolean
}

// Position indicator type
export type PositionIndicator = 'D' | 'SB' | 'BB' | null

