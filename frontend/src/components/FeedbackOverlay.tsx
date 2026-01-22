import { EVResult } from '../types'
import styles from './FeedbackOverlay.module.css'

interface FeedbackOverlayProps {
  result: EVResult | null
  visible: boolean
}

export default function FeedbackOverlay({ result, visible }: FeedbackOverlayProps) {
  if (!visible || !result) return null

  const { wasCorrect, equity, potOdds, explanation } = result

  return (
    <div className={`${styles.overlay} ${wasCorrect ? styles.correct : styles.wrong}`}>
      <div className={styles.content}>
        <div className={styles.result}>
          {wasCorrect ? (
            <>
              <span className={styles.icon}>✓</span>
              <span className={styles.text}>CORRECT</span>
            </>
          ) : (
            <>
              <span className={styles.icon}>✗</span>
              <span className={styles.text}>WRONG</span>
            </>
          )}
        </div>

        {(equity !== null || potOdds !== null) && (
          <div className={styles.stats}>
            {equity !== null && (
              <div className={styles.stat}>
                <span className={styles.statLabel}>Equity</span>
                <span className={styles.statValue}>{Math.round(equity * 100)}%</span>
              </div>
            )}
            {potOdds !== null && (
              <div className={styles.stat}>
                <span className={styles.statLabel}>Pot Odds</span>
                <span className={styles.statValue}>{Math.round(potOdds * 100)}%</span>
              </div>
            )}
          </div>
        )}

        {explanation && (
          <p className={styles.explanation}>{explanation}</p>
        )}
      </div>
    </div>
  )
}

