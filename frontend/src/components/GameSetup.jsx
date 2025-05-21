// frontend/src/components/GameSetup.jsx
import React, { useState } from 'react'
import { Box, Button, VStack, Heading, RadioGroup, Radio, Stack, Select, Text } from '@chakra-ui/react'
import { createGame } from '../services/socketService' // Import the function

const GameSetup = ({ setIsLoading, setError }) => { // onGameCreated is no longer passed directly
    const [gameMode, setGameMode] = useState('PVP')              // PVP, PVE, AVA
    const [selectedAiDifficulty, setSelectedAiDifficulty] = useState('EASY')
    const [ai1Difficulty, setAi1Difficulty] = useState('EASY')
    const [ai2Difficulty, setAi2Difficulty] = useState('EASY')


    const handleCreateGame = async () => {
        setError(null);
        setIsLoading(true);

        let optionsForSocket = {}; // This will be the second argument to createGame

        if (gameMode === 'PVE') {
            optionsForSocket = selectedAiDifficulty; // Pass the difficulty string directly
        } else if (gameMode === 'AVA') {
            optionsForSocket = {
                ai1_difficulty: ai1Difficulty,
                ai2_difficulty: ai2Difficulty
            };
        }
        // For PVP, optionsForSocket remains {}

        console.log(`Attempting to create game via WebSocket: Mode=${gameMode}, Options=${JSON.stringify(optionsForSocket)}`);

        try {
            createGame(gameMode, optionsForSocket);
        } catch (e) {
            console.error("Error initiating game creation:", e);
            setError("Failed to send game creation request.");
            setIsLoading(false);
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
                {gameMode === 'PVE' && (
                    <VStack spacing={3} align="stretch" w="100%">
                        <Text fontSize="sm" color="gray.600">Select AI Difficulty:</Text>
                        <Select
                            value={selectedAiDifficulty} // This was aiDifficulty before, ensure state name matches
                            onChange={(e) => setSelectedAiDifficulty(e.target.value)} // Ensure state name matches
                        >
                            <option value="EASY">Easy</option>
                            <option value="MEDIUM">Medium</option>
                            <option value="HARD">Hard</option>
                        </Select>
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