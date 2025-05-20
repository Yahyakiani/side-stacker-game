import { Box, Heading, Button } from '@chakra-ui/react'
import './App.css'
import GamePage from './pages/GamePage'

function App() {

  return (
    <>
      <Box textAlign="center" p={5}>
        <Heading as="h1" size="xl" mb={6}>
          Side-Stacker Game
        </Heading>
        <Box minH="100vh" bg="gray.50"> {/* Basic page background */}
          <GamePage />
        </Box>
      </Box>
    </>
  )
}

export default App
