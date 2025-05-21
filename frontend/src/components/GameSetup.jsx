// frontend/src/components/GameSetup.jsx
import React, { useState } from 'react'
import { Box, Button, VStack, Heading, RadioGroup, Radio, Stack, Select, Text } from '@chakra-ui/react'
import { createGame } from '../services/socketService' // Import the function

const GameSetup = ({ setIsLoading, setError }) => { // onGameCreated is no longer passed directly
    const [gameMode, setGameMode] = useState('PVP')
    const [aiDifficulty, setAiDifficulty] = useState('EASY')

    const handleCreateGame = async () => {
        setError(null)
        setIsLoading(true)

        let modeForSocket = gameMode
        let difficultyForSocket = null

        if (gameMode === 'PVE') {
            modeForSocket = 'PVE'
            difficultyForSocket = aiDifficulty
        }

        console.log(
            `Attempting to create game via WebSocket: Mode=${modeForSocket}, ` +
            `Difficulty=${difficultyForSocket || 'N/A'}`
        )

        try {
            createGame(modeForSocket, difficultyForSocket)
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
                    <Stack direction="column" spacing={3}>
                        <Radio value="PVP">Player vs Player</Radio>
                        <Radio value="PVE">Player vs AI</Radio>
                    </Stack>
                </RadioGroup>
                {gameMode === 'PVE' && (
                    <VStack spacing={3} align="stretch" w="100%">
                        <Text fontSize="sm" color="gray.600">Select AI Difficulty:</Text>
                        <Select value={aiDifficulty} onChange={e => setAiDifficulty(e.target.value)}>
                            <option value="EASY">Easy</option>
                            <option value="MEDIUM">Medium</option>
                            <option value="HARD" disabled>Hard (Coming Soon)</option>
                        </Select>
                    </VStack>
                )}


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