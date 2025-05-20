// frontend/src/components/GameSetup.jsx
import React, { useState } from 'react'
import { Box, Button, VStack, Heading, RadioGroup, Radio, Stack } from '@chakra-ui/react'
import { createGame } from '../services/socketService' // Import the function

const GameSetup = ({ setIsLoading, setError }) => { // onGameCreated is no longer passed directly
    const [gameMode, setGameMode] = useState('PVP')
    // const [aiDifficulty, setAiDifficulty] = useState('EASY')

    const handleCreateGame = async () => {
        setError(null) // Clear previous errors
        setIsLoading(true)
        console.log(`Attempting to create game via WebSocket: Mode=${gameMode}`)

        try {
            // The socketService.onmessage (and specifically onGameCreatedCallback in GamePage)
            // will handle the response from the server.
            createGame(gameMode /*, aiDifficulty */)
            // setIsLoading(false) will be handled in GamePage when game_created is received or on error
        } catch (e) {
            console.error("Error initiating game creation:", e)
            setError("Failed to send game creation request.")
            setIsLoading(false)
        }
    }

    return (
        <Box p={5} shadow="md" borderWidth="1px" borderRadius="md" maxW="400px" mx="auto" mt="10vh">
            <VStack spacing={6}>
                <Heading as="h2" size="lg">
                    Create New Game
                </Heading>

                <RadioGroup onChange={setGameMode} value={gameMode}>
                    <Stack direction="row" spacing={5}>
                        <Radio value="PVP">Player vs Player</Radio>
                        <Radio value="PVE_TEMP" isDisabled>Player vs AI (Coming Soon)</Radio>
                    </Stack>
                </RadioGroup>

                <Button
                    colorScheme="teal"
                    onClick={handleCreateGame}
                    isLoading={false} // Loading state will be managed by GamePage
                    isFullWidth
                >
                    Create Game
                </Button>
            </VStack>
        </Box>
    )
}

export default GameSetup