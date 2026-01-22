import { Player, PositionIndicator } from '../types'
import CardComponent from './Card'
import styles from './PlayerSeat.module.css'

interface PlayerSeatProps {
  player: Player
  isCurrentTurn: boolean
  positionIndicator: PositionIndicator
  seatAngle: number
  showAggression?: boolean
  showTightness?: boolean
}

export default function PlayerSeat({
  player,
  isCurrentTurn,
  positionIndicator,
  seatAngle,
  showAggression = true,
  showTightness = true,
}: PlayerSeatProps) {
  const { name, chips, holeCards, isHuman, isFolded, currentBet, isActive } = player

  // Determine if cards should be above or below based on seat position
  const cardsOnTop = seatAngle > 90 && seatAngle < 270

  // Show cards face up if we have the actual card data (human or showdown)
  const showCardsFaceUp = holeCards !== null && holeCards.length > 0

  // Player is eliminated if they have 0 chips
  const isEliminated = chips === 0 && !isActive

  return (
    <div className={`${styles.seat} ${isCurrentTurn ? styles.active : ''} ${isFolded ? styles.folded : ''} ${isEliminated ? styles.eliminated : ''}`}>
      {/* Position indicator */}
      {positionIndicator && (
        <div className={`${styles.positionChip} ${styles[positionIndicator.toLowerCase()]}`}>
          {positionIndicator}
        </div>
      )}

      {/* Cards - position varies based on seat location */}
      {!cardsOnTop && showCardsFaceUp && (
        <div className={styles.cardsTop}>
          {holeCards!.map((card, i) => (
            <CardComponent
              key={i}
              card={card}
              small
              faceDown={false}
              folded={isFolded}
            />
          ))}
        </div>
      )}

      {/* Hidden cards for opponents (when we don't have their card data) */}
      {!cardsOnTop && !showCardsFaceUp && !isHuman && !isFolded && player.isActive && (
        <div className={styles.cardsTop}>
          <CardComponent faceDown small />
          <CardComponent faceDown small />
        </div>
      )}

      {/* Player info box */}
      <div className={styles.infoBox}>
        <div className={styles.avatar}>
          {isHuman ? '👤' : '🤖'}
        </div>
        <div className={styles.details}>
          <span className={styles.name}>{name}</span>
          <span className={styles.chips}>{chips.toLocaleString()}</span>
          {!isHuman && (showAggression || showTightness) && (
            <span className={styles.playerStyle}>
              {showAggression && player.aggression !== null && `A:${Math.round(player.aggression * 100)}%`}
              {showAggression && showTightness && player.aggression !== null && player.tightness !== null && ' '}
              {showTightness && player.tightness !== null && `T:${Math.round(player.tightness * 100)}%`}
            </span>
          )}
        </div>
        {isCurrentTurn && <div className={styles.turnIndicator} />}
      </div>

      {/* Current bet */}
      {currentBet > 0 && (
        <div className={styles.betChip}>
          <span>{currentBet}</span>
        </div>
      )}

      {/* Cards below for top-half seats */}
      {cardsOnTop && showCardsFaceUp && (
        <div className={styles.cardsBottom}>
          {holeCards!.map((card, i) => (
            <CardComponent
              key={i}
              card={card}
              small
              faceDown={false}
              folded={isFolded}
            />
          ))}
        </div>
      )}

      {/* Hidden cards for top-half opponents */}
      {cardsOnTop && !showCardsFaceUp && !isHuman && !isFolded && player.isActive && (
        <div className={styles.cardsBottom}>
          <CardComponent faceDown small />
          <CardComponent faceDown small />
        </div>
      )}

      {/* Folded indicator */}
      {isFolded && !isEliminated && (
        <div className={styles.foldedBadge}>FOLD</div>
      )}

      {/* Eliminated indicator */}
      {isEliminated && (
        <div className={styles.eliminatedBadge}>OUT</div>
      )}
    </div>
  )
}

