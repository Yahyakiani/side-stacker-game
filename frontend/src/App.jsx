import { Box, useColorModeValue } from '@chakra-ui/react'
import GamePage from './pages/GamePage'
import './App.css'

function App() {

  const bgColor = useColorModeValue('gray.50', 'gray.800') // Light for light, dark for dark
  const textColor = useColorModeValue('gray.800', 'whiteAlpha.900')

  return (
    <>
      <Box minH="100vh" bg={bgColor} color={textColor}>
        <GamePage />
      </Box>
    </>
  )
}

export default App
