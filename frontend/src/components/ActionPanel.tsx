import { useState, useEffect } from 'react'
import { ActionType } from '../types'
import styles from './ActionPanel.module.css'

interface ActionPanelProps {
  availableActions: ActionType[]
  currentBet: number
  playerBet: number
  playerChips: number
  minRaise: number
  maxRaise: number
  pot: number
  onAction: (action: ActionType, amount?: number) => void
  disabled: boolean
}

export default function ActionPanel({
  availableActions,
  currentBet,
  playerBet,
  playerChips,
  minRaise,
  maxRaise,
  pot,
  onAction,
  disabled,
}: ActionPanelProps) {
  const [raiseAmount, setRaiseAmount] = useState(minRaise)
  const [showRaiseSlider, setShowRaiseSlider] = useState(false)

  const callAmount = currentBet - playerBet
  const canCheck = availableActions.includes('check')
  const canCall = availableActions.includes('call') && callAmount > 0
  const canBet = availableActions.includes('bet')
  const canRaise = availableActions.includes('raise')
  const canFold = availableActions.includes('fold')

  useEffect(() => {
    setRaiseAmount(minRaise)
  }, [minRaise])

  const handleFold = () => {
    if (disabled) return
    onAction('fold')
  }

  const handleCheckCall = () => {
    if (disabled) return
    if (canCheck) {
      onAction('check')
    } else if (canCall) {
      onAction('call', callAmount)
    }
  }

  const handleBetRaise = () => {
    if (disabled) return
    if (!showRaiseSlider) {
      setShowRaiseSlider(true)
      return
    }
    if (canBet) {
      onAction('bet', raiseAmount)
    } else if (canRaise) {
      onAction('raise', raiseAmount)
    }
    setShowRaiseSlider(false)
  }

  const handleSliderChange = (value: number) => {
    setRaiseAmount(value)
  }

  const presetAmounts = [
    { label: '½ Pot', value: Math.floor(pot / 2) },
    { label: 'Pot', value: pot },
    { label: '2x Pot', value: pot * 2 },
    { label: 'All In', value: maxRaise },
  ].filter(p => p.value >= minRaise && p.value <= maxRaise)

  return (
    <div className={`${styles.panel} ${disabled ? styles.disabled : ''}`}>
      {showRaiseSlider && (
        <div className={styles.raiseControls}>
          <div className={styles.raiseHeader}>
            <span className={styles.raiseLabel}>
              {canBet ? 'BET' : 'RAISE TO'}
            </span>
            <span className={styles.raiseValue}>{raiseAmount}</span>
          </div>
          
          <input
            type="range"
            className={styles.slider}
            min={minRaise}
            max={maxRaise}
            value={raiseAmount}
            onChange={e => handleSliderChange(parseInt(e.target.value))}
          />
          
          <div className={styles.presets}>
            {presetAmounts.map((preset, i) => (
              <button
                key={i}
                className={styles.presetButton}
                onClick={() => setRaiseAmount(preset.value)}
              >
                {preset.label}
              </button>
            ))}
          </div>

          <div className={styles.raiseActions}>
            <button
              className={styles.cancelRaiseButton}
              onClick={() => setShowRaiseSlider(false)}
            >
              CANCEL
            </button>
            <button
              className={styles.confirmRaiseButton}
              onClick={handleBetRaise}
            >
              {canBet ? 'BET' : 'RAISE'} {raiseAmount}
            </button>
          </div>
        </div>
      )}

      {!showRaiseSlider && (
        <div className={styles.buttons}>
          <button
            className={`${styles.actionButton} ${styles.foldButton}`}
            onClick={handleFold}
            disabled={disabled || !canFold}
          >
            FOLD
          </button>

          <button
            className={`${styles.actionButton} ${styles.checkCallButton}`}
            onClick={handleCheckCall}
            disabled={disabled || (!canCheck && !canCall)}
          >
            {canCheck ? 'CHECK' : `CALL ${callAmount}`}
          </button>

          <button
            className={`${styles.actionButton} ${styles.betRaiseButton}`}
            onClick={handleBetRaise}
            disabled={disabled || (!canBet && !canRaise)}
          >
            {canBet ? 'BET' : 'RAISE'}
          </button>
        </div>
      )}


      {disabled && (
        <div className={styles.waitingOverlay}>
          <span>Waiting for other players...</span>
        </div>
      )}
    </div>
  )
}

