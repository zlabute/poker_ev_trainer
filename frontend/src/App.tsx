import { Routes, Route } from 'react-router-dom'
import StartScreen from './screens/StartScreen'
import SettingsScreen from './screens/SettingsScreen'
import GameScreen from './screens/GameScreen'

function App() {
  return (
    <Routes>
      <Route path="/" element={<StartScreen />} />
      <Route path="/settings" element={<SettingsScreen />} />
      <Route path="/game" element={<GameScreen />} />
    </Routes>
  )
}

export default App

