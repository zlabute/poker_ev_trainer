import { GameState } from '../types'
import PlayerSeat from './PlayerSeat'
import CardComponent from './Card'
import styles from './PokerTable.module.css'

interface PokerTableProps {
  gameState: GameState
  currentPlayerPosition: number
  showAggression?: boolean
  showTightness?: boolean
}

// Calculate seat positions around an elliptical table
function getSeatPositions(numPlayers: number): { x: number; y: number; angle: number }[] {
  const positions: { x: number; y: number; angle: number }[] = []
  
  // Human player always at bottom (position 0)
  // Other players distributed around the table clockwise
  for (let i = 0; i < numPlayers; i++) {
    // Start from bottom (270 degrees) and go clockwise
    const angle = (270 + (i * 360) / numPlayers) % 360
    const radians = (angle * Math.PI) / 180
    
    // Ellipse with different x and y radii
    const xRadius = 42 // % from center
    const yRadius = 38 // % from center
    
    const x = 50 + xRadius * Math.cos(radians)
    const y = 50 + yRadius * Math.sin(radians)
    
    positions.push({ x, y, angle })
  }
  
  return positions
}

export default function PokerTable({ gameState, currentPlayerPosition, showAggression = true, showTightness = true }: PokerTableProps) {
  const { players, communityCards, pot, dealerPosition } = gameState
  const seatPositions = getSeatPositions(players.length)

  // Determine position indicators
  const getPositionIndicator = (playerPosition: number) => {
    if (playerPosition === dealerPosition) return 'D'
    const sbPosition = (dealerPosition + 1) % players.length
    const bbPosition = (dealerPosition + 2) % players.length
    if (playerPosition === sbPosition) return 'SB'
    if (playerPosition === bbPosition) return 'BB'
    return null
  }

  return (
    <div className={styles.tableContainer}>
      {/* Table surface */}
      <div className={styles.table}>
        <div className={styles.tableInner}>
          <div className={styles.feltPattern} />
          
          {/* Center area - pot and community cards */}
          <div className={styles.centerArea}>
            <div className={styles.pot}>
              <span className={styles.potLabel}>POT</span>
              <span className={styles.potValue}>{pot}</span>
            </div>
            
            <div className={styles.communityCards}>
              {communityCards.map((card, i) => (
                <CardComponent key={i} card={card} delay={i * 0.1} />
              ))}
              {/* Empty slots for remaining cards */}
              {Array.from({ length: 5 - communityCards.length }).map((_, i) => (
                <div key={`empty-${i}`} className={styles.emptyCardSlot} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Player seats */}
      {players.map((player, index) => {
        const pos = seatPositions[index]
        return (
          <div
            key={player.id}
            className={styles.seatWrapper}
            style={{
              left: `${pos.x}%`,
              top: `${pos.y}%`,
            }}
          >
            <PlayerSeat
              player={player}
              isCurrentTurn={index === currentPlayerPosition}
              positionIndicator={getPositionIndicator(index)}
              seatAngle={pos.angle}
              showAggression={showAggression}
              showTightness={showTightness}
            />
          </div>
        )
      })}
    </div>
  )
}

