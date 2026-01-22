import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { GameSettings, AggressionLevel, TightnessLevel } from '../types'
import styles from './SettingsScreen.module.css'

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

const AGGRESSION_OPTIONS: { value: AggressionLevel; label: string; description: string }[] = [
  { value: 'passive', label: 'Passive', description: 'Bots bet small and rarely bluff' },
  { value: 'medium', label: 'Medium', description: 'Balanced bet sizing' },
  { value: 'aggressive', label: 'Aggressive', description: 'Bots bet big and bluff often' },
  { value: 'random', label: 'Random', description: 'Each bot has random aggression' },
]

const TIGHTNESS_OPTIONS: { value: TightnessLevel; label: string; description: string }[] = [
  { value: 'loose', label: 'Loose', description: 'Bots play many hands, call often' },
  { value: 'medium', label: 'Medium', description: 'Balanced hand selection' },
  { value: 'tight', label: 'Tight', description: 'Bots only play strong hands' },
  { value: 'random', label: 'Random', description: 'Each bot has random tightness' },
]

export default function SettingsScreen() {
  const navigate = useNavigate()
  const [settings, setSettings] = useState<GameSettings>(DEFAULT_SETTINGS)
  const [validationError, setValidationError] = useState<string | null>(null)

  useEffect(() => {
    const saved = localStorage.getItem('pokerSettings')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        // Ensure all fields exist with defaults
        setSettings({
          ...DEFAULT_SETTINGS,
          ...parsed,
        })
      } catch {
        // Use defaults if parse fails
      }
    }
  }, [])

  // Validate settings
  useEffect(() => {
    const { startingChips, smallBlind, bigBlind } = settings

    if (bigBlind !== smallBlind * 2) {
      setValidationError('Big blind must be exactly 2x small blind')
    } else if (bigBlind > startingChips * 0.5) {
      setValidationError('Big blind cannot exceed 50% of starting chips')
    } else if (smallBlind < 1) {
      setValidationError('Small blind must be at least 1')
    } else {
      setValidationError(null)
    }
  }, [settings])

  const handleSave = () => {
    if (validationError) return
    localStorage.setItem('pokerSettings', JSON.stringify(settings))
    navigate('/')
  }

  const handleBack = () => {
    navigate('/')
  }

  const updateSetting = <K extends keyof GameSettings>(
    key: K,
    value: GameSettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const updateSmallBlind = (value: number) => {
    const sb = Math.max(1, value)
    setSettings(prev => ({
      ...prev,
      smallBlind: sb,
      bigBlind: sb * 2,
    }))
  }

  return (
    <div className={styles.container}>
      <div className={styles.backgroundGlow} />

      <div className={styles.content}>
        <h1 className={styles.title}>SETTINGS</h1>

        <div className={styles.settingsCard}>
          <div className={styles.settingGroup}>
            <label className={styles.label}>Starting Chips</label>
            <div className={styles.inputWrapper}>
              <span className={styles.chipIcon}>💰</span>
              <input
                type="number"
                className={styles.input}
                value={settings.startingChips}
                onChange={e => updateSetting('startingChips', Math.max(100, parseInt(e.target.value) || 100))}
                min={100}
                max={100000}
                step={100}
              />
            </div>
            <span className={styles.hint}>Min: 100 | Max: 100,000</span>
          </div>

          <div className={styles.settingGroup}>
            <label className={styles.label}>Small Blind</label>
            <div className={styles.inputWrapper}>
              <span className={styles.chipIcon}>🎯</span>
              <input
                type="number"
                className={styles.input}
                value={settings.smallBlind}
                onChange={e => updateSmallBlind(parseInt(e.target.value) || 1)}
                min={1}
                max={Math.floor(settings.startingChips * 0.25)}
                step={1}
              />
            </div>
            <span className={styles.hint}>Big blind will be {settings.smallBlind * 2} (2x small blind)</span>
          </div>

          <div className={styles.settingGroup}>
            <label className={styles.label}>Number of Opponents</label>
            <div className={styles.sliderWrapper}>
              <input
                type="range"
                className={styles.slider}
                value={settings.numOpponents}
                onChange={e => updateSetting('numOpponents', parseInt(e.target.value))}
                min={1}
                max={8}
              />
              <div className={styles.sliderValue}>{settings.numOpponents}</div>
            </div>
            <div className={styles.sliderLabels}>
              <span>1</span>
              <span>Heads Up</span>
              <span>8</span>
            </div>
          </div>

          <div className={styles.settingGroup}>
            <label className={styles.label}>CPU Aggression Level</label>
            <p className={styles.settingDescription}>Controls bet sizing, raise frequency, and bluff frequency</p>
            <div className={styles.aggressionOptions}>
              {AGGRESSION_OPTIONS.map(option => (
                <button
                  key={option.value}
                  className={`${styles.aggressionButton} ${settings.aggressionLevel === option.value ? styles.aggressionActive : ''}`}
                  onClick={() => updateSetting('aggressionLevel', option.value)}
                >
                  <span className={styles.aggressionLabel}>{option.label}</span>
                  <span className={styles.aggressionDesc}>{option.description}</span>
                </button>
              ))}
            </div>
            <label className={styles.toggleRow}>
              <span className={styles.toggleLabel}>Show aggression % on players</span>
              <div
                className={`${styles.toggle} ${settings.showAggression ? styles.toggleOn : ''}`}
                onClick={() => updateSetting('showAggression', !settings.showAggression)}
              >
                <div className={styles.toggleKnob} />
              </div>
            </label>
          </div>

          <div className={styles.settingGroup}>
            <label className={styles.label}>CPU Tightness Level</label>
            <p className={styles.settingDescription}>Controls hand selection and calling thresholds</p>
            <div className={styles.aggressionOptions}>
              {TIGHTNESS_OPTIONS.map(option => (
                <button
                  key={option.value}
                  className={`${styles.aggressionButton} ${settings.tightnessLevel === option.value ? styles.aggressionActive : ''}`}
                  onClick={() => updateSetting('tightnessLevel', option.value)}
                >
                  <span className={styles.aggressionLabel}>{option.label}</span>
                  <span className={styles.aggressionDesc}>{option.description}</span>
                </button>
              ))}
            </div>
            <label className={styles.toggleRow}>
              <span className={styles.toggleLabel}>Show tightness % on players</span>
              <div
                className={`${styles.toggle} ${settings.showTightness ? styles.toggleOn : ''}`}
                onClick={() => updateSetting('showTightness', !settings.showTightness)}
              >
                <div className={styles.toggleKnob} />
              </div>
            </label>
          </div>

          {validationError && (
            <div className={styles.errorMessage}>
              ⚠️ {validationError}
            </div>
          )}

          <div className={styles.summary}>
            <div className={styles.summaryItem}>
              <span>Players at table:</span>
              <span className={styles.summaryValue}>{settings.numOpponents + 1}</span>
            </div>
            <div className={styles.summaryItem}>
              <span>Blinds:</span>
              <span className={styles.summaryValue}>
                {settings.smallBlind}/{settings.bigBlind}
              </span>
            </div>
            <div className={styles.summaryItem}>
              <span>Starting big blinds:</span>
              <span className={styles.summaryValue}>
                {Math.floor(settings.startingChips / settings.bigBlind)} BB
              </span>
            </div>
          </div>
        </div>

        <div className={styles.buttons}>
          <button
            className={`${styles.saveButton} ${validationError ? styles.disabled : ''}`}
            onClick={handleSave}
            disabled={!!validationError}
          >
            SAVE
          </button>
          <button className={styles.backButton} onClick={handleBack}>
            BACK
          </button>
        </div>
      </div>
    </div>
  )
}

