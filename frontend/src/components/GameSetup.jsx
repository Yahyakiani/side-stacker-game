// frontend/src/components/GameSetup.jsx
import React, { useState } from 'react'
import { Box, Button, VStack, Heading, RadioGroup, Radio, Stack, Select, Text } from '@chakra-ui/react'
import { createGame } from '../services/socketService' // Import the function

const GameSetup = ({ setIsLoading, setError }) => { // onGameCreated is no longer passed directly
    const [gameMode, setGameMode] = useState('PVP')              // PVP, PVE, AVA
    const [pveAiDifficulty, setPveAiDifficulty] = useState('EASY')
    const [ai1Difficulty, setAi1Difficulty] = useState('EASY')
    const [ai2Difficulty, setAi2Difficulty] = useState('EASY')


    const handleCreateGame = async () => {
        setError(null)
        setIsLoading(true)

        let modeForSocket = gameMode
        let payloadDetails = {}

        if (gameMode === 'PVE') {
            payloadDetails.difficulty = pveAiDifficulty
        } else if (gameMode === 'AVA') {
            payloadDetails.ai1_difficulty = ai1Difficulty
            payloadDetails.ai2_difficulty = ai2Difficulty
        }

        console.log(`Attempting to create game: Mode=${modeForSocket}, Details=${JSON.stringify(payloadDetails)}`)

        try {
            createGame(modeForSocket, payloadDetails)
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
                        <Radio value="AVA">AI vs AI (Spectate)</Radio>
                    </Stack>
                </RadioGroup>
                {gameMode === 'AVA' && (
                    <VStack spacing={4} align="stretch" w="100%">
                        <VStack spacing={1} align="stretch">
                            <Text fontSize="sm" color="gray.600">AI 1 (Plays as X):</Text>
                            <Select value={ai1Difficulty} onChange={e => setAi1Difficulty(e.target.value)}>
                                <option value="EASY">Easy</option>
                                <option value="MEDIUM">Medium</option>
                                <option value="HARD">Hard</option>
                            </Select>
                        </VStack>
                        <VStack spacing={1} align="stretch">
                            <Text fontSize="sm" color="gray.600">AI 2 (Plays as O):</Text>
                            <Select value={ai2Difficulty} onChange={e => setAi2Difficulty(e.target.value)}>
                                <option value="EASY">Easy</option>
                                <option value="MEDIUM">Medium</option>
                                <option value="HARD">Hard</option>
                            </Select>
                        </VStack>
                    </VStack>
                )}



                <Button
                    colorScheme="teal"
                    onClick={handleCreateGame}
                    isLoading={false} // Loading state will be managed by GamePage
                    width="full"
                >
                    Create Game
                </Button>
            </VStack>
        </Box>
    )
}

export default GameSetup