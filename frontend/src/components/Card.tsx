import { Card } from '../types'
import styles from './Card.module.css'

interface CardProps {
  card?: Card
  faceDown?: boolean
  small?: boolean
  folded?: boolean
  delay?: number
}

const suitSymbols: Record<string, string> = {
  h: '♥',
  d: '♦',
  c: '♣',
  s: '♠',
}

const suitColors: Record<string, 'red' | 'black'> = {
  h: 'red',
  d: 'red',
  c: 'black',
  s: 'black',
}

export default function CardComponent({ 
  card, 
  faceDown = false, 
  small = false,
  folded = false,
  delay = 0,
}: CardProps) {
  const showFace = card && !faceDown

  return (
    <div 
      className={`
        ${styles.card} 
        ${small ? styles.small : ''} 
        ${folded ? styles.folded : ''}
        ${faceDown ? styles.faceDown : ''}
      `}
      style={{ animationDelay: `${delay}s` }}
    >
      {showFace ? (
        <div className={`${styles.face} ${styles[suitColors[card.suit]]}`}>
          <span className={styles.rank}>{card.rank}</span>
          <span className={styles.suit}>{suitSymbols[card.suit]}</span>
          <span className={styles.cornerRank}>{card.rank}</span>
          <span className={styles.cornerSuit}>{suitSymbols[card.suit]}</span>
        </div>
      ) : (
        <div className={styles.back}>
          <div className={styles.backPattern}>
            <div className={styles.backInner} />
          </div>
        </div>
      )}
    </div>
  )
}

