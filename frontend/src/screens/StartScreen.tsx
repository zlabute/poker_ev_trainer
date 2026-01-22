import { useNavigate } from 'react-router-dom'
import styles from './StartScreen.module.css'

export default function StartScreen() {
    const navigate = useNavigate()

    return (
        <div className={styles.container}>
            <div className={styles.backgroundGlow} />

            <div className={styles.content}>
                <div className={styles.titleSection}>
                    <h1 className={styles.title}>POKER</h1>
                    <h2 className={styles.subtitle}>EV TRAINER</h2>
                    <p className={styles.tagline}>Master optimal decisions</p>
                </div>

                <div className={styles.cardFan}>
                    <div className={`${styles.card} ${styles.card1}`}>
                        <span className={styles.cardRank}>A</span>
                        <span className={styles.cardSuit}>♠</span>
                    </div>
                    <div className={`${styles.card} ${styles.card2}`}>
                        <span className={styles.cardRank}>K</span>
                        <span className={`${styles.cardSuit} ${styles.red}`}>♥</span>
                    </div>
                </div>

                <div className={styles.buttons}>
                    <button
                        className={styles.playButton}
                        onClick={() => navigate('/game')}
                    >
                        PLAY
                    </button>
                    <button
                        className={styles.settingsButton}
                        onClick={() => navigate('/settings')}
                    >
                        SETTINGS
                    </button>
                </div>
            </div>

            <div className={styles.chips}>
                <div className={`${styles.chip} ${styles.chipRed}`} />
                <div className={`${styles.chip} ${styles.chipBlue}`} />
                <div className={`${styles.chip} ${styles.chipGreen}`} />
            </div>
        </div>
    )
}

