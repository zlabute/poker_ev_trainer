import { GameState, GameSettings, ActionType, EVResult } from '../types'

const API_BASE = '/api'

interface ActionResponse {
  success: boolean
  ev_result: EVResult | null
  game_state: GameState
  hand_complete: boolean
  winner_id: string | null
}

// Convert snake_case response to camelCase
function transformGameState(data: any): GameState {
  return {
    id: data.id,
    players: data.players.map((p: any) => ({
      id: p.id,
      name: p.name,
      chips: p.chips,
      holeCards: p.hole_cards?.map((c: any) => ({
        suit: c.suit,
        rank: c.rank,
        code: c.code,
      })) || null,
      isHuman: p.is_human,
      isActive: p.is_active,
      isAllIn: p.is_all_in,
      currentBet: p.current_bet,
      position: p.position,
      isFolded: p.is_folded,
      aggression: p.aggression,
      tightness: p.tightness,
    })),
    communityCards: data.community_cards.map((c: any) => ({
      suit: c.suit,
      rank: c.rank,
      code: c.code,
    })),
    pot: data.pot,
    currentBet: data.current_bet,
    dealerPosition: data.dealer_position,
    currentPlayer: data.current_player,
    phase: data.phase,
    smallBlind: data.small_blind,
    bigBlind: data.big_blind,
    availableActions: data.available_actions,
    minRaise: data.min_raise,
    maxRaise: data.max_raise,
  }
}

function transformEVResult(data: any): EVResult | null {
  if (!data) return null
  return {
    userAction: data.user_action,
    optimalAction: data.optimal_action,
    wasCorrect: data.was_correct,
    equity: data.equity,
    potOdds: data.pot_odds,
    explanation: data.explanation,
  }
}

export async function createGame(settings: GameSettings): Promise<GameState> {
  const response = await fetch(`${API_BASE}/game/new`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      starting_chips: settings.startingChips,
      small_blind: settings.smallBlind,
      big_blind: settings.bigBlind,
      num_opponents: settings.numOpponents,
      aggression_level: settings.aggressionLevel,
      tightness_level: settings.tightnessLevel,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to create game')
  }

  const data = await response.json()
  return transformGameState(data)
}

export async function getGameState(gameId: string): Promise<GameState> {
  const response = await fetch(`${API_BASE}/game/${gameId}`)

  if (!response.ok) {
    throw new Error('Failed to get game state')
  }

  const data = await response.json()
  return transformGameState(data)
}

export async function submitAction(
  gameId: string,
  action: ActionType,
  amount?: number
): Promise<{ gameState: GameState; evResult: EVResult | null; handComplete: boolean; winnerId: string | null }> {
  const response = await fetch(`${API_BASE}/game/${gameId}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, amount }),
  })

  if (!response.ok) {
    throw new Error('Failed to submit action')
  }

  const data: ActionResponse = await response.json()
  return {
    gameState: transformGameState(data.game_state),
    evResult: transformEVResult(data.ev_result),
    handComplete: data.hand_complete,
    winnerId: data.winner_id,
  }
}

export async function cpuAction(gameId: string): Promise<GameState> {
  const response = await fetch(`${API_BASE}/game/${gameId}/cpu-action`, {
    method: 'POST',
  })

  if (!response.ok) {
    throw new Error('Failed to execute CPU action')
  }

  const data = await response.json()
  return transformGameState(data)
}

export async function nextHand(gameId: string): Promise<GameState> {
  const response = await fetch(`${API_BASE}/game/${gameId}/next-hand`, {
    method: 'POST',
  })

  if (!response.ok) {
    throw new Error('Failed to start next hand')
  }

  const data = await response.json()
  return transformGameState(data)
}

export async function deleteGame(gameId: string): Promise<void> {
  await fetch(`${API_BASE}/game/${gameId}`, {
    method: 'DELETE',
  })
}

