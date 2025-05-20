import { Box, Heading, Button } from '@chakra-ui/react'
import './App.css'

function App() {

  return (
    <>
      <Box textAlign="center" p={5}>
        <Heading as="h1" size="xl" mb={6}>
          Side-Stacker Game (Chakra UI Test)
        </Heading>
        <Button colorScheme="teal" size="lg" onClick={() => alert('Chakra Button Clicked!')}>
          Test Button
        </Button>
      </Box>
    </>
  )
}

export default App
