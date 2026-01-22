import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import PokerTable from '../components/PokerTable'
import ActionPanel from '../components/ActionPanel'
import FeedbackOverlay from '../components/FeedbackOverlay'
import { GameState, GameSettings, ActionType, EVResult } from '../types'
import * as api from '../services/api'
import styles from './GameScreen.module.css'

const DEFAULT_SETTINGS: GameSettings = {
  startingChips: 1000,
  smallBlind: 10,
  bigBlind: 20,
  numOpponents: 5,
  aggressionLevel: 'medium',
  tightnessLevel: 'medium',
  showAggression: true,
  showTightness: true,
}

export default function GameScreen() {
  const navigate = useNavigate()
  const [settings, setSettings] = useState<GameSettings>(DEFAULT_SETTINGS)
  const [gameState, setGameState] = useState<GameState | null>(null)
  const [feedback, setFeedback] = useState<EVResult | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [processingCPU, setProcessingCPU] = useState(false)
  const initRef = useRef(false)

  // Initialize game (with protection against StrictMode double-render)
  useEffect(() => {
    if (initRef.current) return
    initRef.current = true

    const initGame = async () => {
      try {
        // Load settings from localStorage
        const saved = localStorage.getItem('pokerSettings')
        const loadedSettings = saved ? JSON.parse(saved) : DEFAULT_SETTINGS
        setSettings(loadedSettings)

        // Create new game via API
        const state = await api.createGame(loadedSettings)
        setGameState(state)
        setLoading(false)
      } catch (err) {
        console.error('Failed to create game:', err)
        setError('Failed to connect to game server')
        setLoading(false)
      }
    }

    initGame()
  }, [])

  // Process CPU turns
  const processCPUTurns = useCallback(async () => {
    if (!gameState || processingCPU) return

    const currentPlayer = gameState.players[gameState.currentPlayer]

    // If it's not human's turn and game is active, process CPU
    if (!currentPlayer.isHuman && gameState.phase !== 'showdown' && gameState.phase !== 'waiting') {
      setProcessingCPU(true)

      try {
        // Add delay for realism (3 seconds)
        await new Promise(resolve => setTimeout(resolve, 1500))

        const newState = await api.cpuAction(gameState.id)
        setGameState(newState)

        // Check if hand is complete
        const activePlayers = newState.players.filter(p => p.isActive && !p.isFolded)
        if (activePlayers.length <= 1 || newState.phase === 'showdown') {
          // Hand is complete - show cards for 10 seconds then start next hand
          setTimeout(async () => {
            try {
              const nextState = await api.nextHand(gameState.id)
              setGameState(nextState)
            } catch (err) {
              console.error('Failed to start next hand:', err)
            }
          }, 10000)
        }
      } catch (err) {
        console.error('CPU action failed:', err)
      } finally {
        setProcessingCPU(false)
      }
    }
  }, [gameState, processingCPU])

  // Trigger CPU processing when game state changes
  useEffect(() => {
    if (gameState && !showFeedback) {
      processCPUTurns()
    }
  }, [gameState, showFeedback, processCPUTurns])

  const handleAction = async (action: ActionType, amount?: number) => {
    if (!gameState) return

    try {
      const result = await api.submitAction(gameState.id, action, amount)

      // Show feedback
      if (result.evResult) {
        setFeedback(result.evResult)
        setShowFeedback(true)
      }

      // Update game state after feedback delay
      setTimeout(() => {
        setShowFeedback(false)
        setGameState(result.gameState)

        // If hand is complete, show cards for 10 seconds then start next hand
        if (result.handComplete) {
          setTimeout(async () => {
            try {
              const nextState = await api.nextHand(gameState.id)
              setGameState(nextState)
            } catch (err) {
              console.error('Failed to start next hand:', err)
            }
          }, 10000)
        }
      }, 2500)
    } catch (err) {
      console.error('Action failed:', err)
    }
  }

  const handleExit = async () => {
    if (gameState) {
      try {
        await api.deleteGame(gameState.id)
      } catch (err) {
        // Ignore errors on exit
      }
    }
    navigate('/')
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <p>Setting up table...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.loading}>
        <p className={styles.error}>{error}</p>
        <button onClick={() => navigate('/')} className={styles.backButton}>
          Back to Menu
        </button>
      </div>
    )
  }

  if (!gameState) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <p>Loading...</p>
      </div>
    )
  }

  const humanPlayer = gameState.players.find(p => p.isHuman)
  const isHumanTurn = gameState.currentPlayer === humanPlayer?.position && !processingCPU

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button className={styles.exitButton} onClick={handleExit}>
          ✕ EXIT
        </button>
        <div className={styles.blindsInfo}>
          Blinds: {gameState.smallBlind}/{gameState.bigBlind}
        </div>
      </div>

      <div className={styles.tableArea}>
        <PokerTable
          gameState={gameState}
          currentPlayerPosition={gameState.currentPlayer}
          showAggression={settings.showAggression}
          showTightness={settings.showTightness}
        />
      </div>

      <div className={styles.actionArea}>
        <ActionPanel
          availableActions={gameState.availableActions}
          currentBet={gameState.currentBet}
          playerBet={humanPlayer?.currentBet || 0}
          playerChips={humanPlayer?.chips || 0}
          minRaise={gameState.minRaise}
          maxRaise={gameState.maxRaise}
          pot={gameState.pot}
          onAction={handleAction}
          disabled={!isHumanTurn || showFeedback}
        />
      </div>

      <FeedbackOverlay
        result={feedback}
        visible={showFeedback}
      />
    </div>
  )
}
