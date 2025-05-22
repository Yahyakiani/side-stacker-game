// frontend/src/components/GameSetup.jsx
import React, { useState } from 'react';
import {
    Box, Button, VStack, Heading, RadioGroup, Radio, Stack, Select, Text,
    Input,
    useToast,
    FormControl, FormLabel,
    Tabs, TabList, Tab, TabPanels, TabPanel
} from '@chakra-ui/react';
import { createGame, joinGame } from '../services/socketService';
import { GAME_MODES, AI_DIFFICULTY } from '../constants/gameConstants'; 

const GameSetup = ({ setIsLoading, setError, isLoading }) => {
    const [tabIndex, setTabIndex] = useState(0); // 0 for Create, 1 for Join

    // Create Game State
    const [createGameMode, setCreateGameMode] = useState(GAME_MODES.PVP);
    const [pveAiDifficulty, setPveAiDifficulty] = useState(AI_DIFFICULTY.EASY);
    const [avaAi1Difficulty, setAvaAi1Difficulty] = useState(AI_DIFFICULTY.EASY);
    const [avaAi2Difficulty, setAvaAi2Difficulty] = useState(AI_DIFFICULTY.EASY);

    // Join Game State
    const [joinGameId, setJoinGameId] = useState('');
    const toast = useToast();

    const handleCreateGame = async () => {
        setError(null);
        setIsLoading(true);

        let optionsForSocket = {};
        if (createGameMode === GAME_MODES.PVE) {
            optionsForSocket = pveAiDifficulty;
        } else if (createGameMode === GAME_MODES.AVA) {
            optionsForSocket = {
                ai1_difficulty: avaAi1Difficulty,
                ai2_difficulty: avaAi2Difficulty
            };
        }
        console.log(`Attempting to create game: Mode=${createGameMode}, Options=${JSON.stringify(optionsForSocket)}`);
        createGame(createGameMode, optionsForSocket);
        // Loading/error state is handled by GamePage based on WebSocket responses
    };

    const handleJoinGame = async () => {
        if (!joinGameId.trim()) {
            toast({ title: "Game ID required", description: "Please enter a Game ID to join.", status: "warning", duration: 3000, isClosable: true });
            return;
        }
        setError(null);
        setIsLoading(true);
        console.log(`Attempting to join game: ID=${joinGameId}`);
        joinGame(joinGameId.trim());
        // Loading/error state is handled by GamePage based on WebSocket responses
    };

    return (
        <Box p={5} shadow="md" borderWidth="1px" borderRadius="md" maxW="400px" mx="auto" mt="10vh">
            <Tabs index={tabIndex} onChange={(index) => setTabIndex(index)} variant="soft-rounded" colorScheme="teal">
                <TabList mb={4} justifyContent="center">
                    <Tab>Create Game</Tab>
                    <Tab>Join Game (PvP)</Tab>
                </TabList>
                <TabPanels>
                    <TabPanel p={0}> {/* Create Game Panel */}
            <VStack spacing={6}>
                            <Heading as="h2" size="lg" textAlign="center">Create New Game</Heading>
                            <RadioGroup onChange={setCreateGameMode} value={createGameMode}>
                                <Stack direction="column" spacing={3}>
                                    <Radio value="PVP">Player vs Player</Radio>
                                    <Radio value="PVE">Player vs AI</Radio>
                                    <Radio value="AVA">AI vs AI (Spectate)</Radio>
                                </Stack>
                            </RadioGroup>

                            {createGameMode === 'PVE' && ( /* ... PVE Difficulty Select ... */
                                <VStack spacing={3} align="stretch" w="100%">
                                    <Text fontSize="sm" color="gray.600">Select AI Difficulty:</Text>
                                    <Select value={pveAiDifficulty} onChange={(e) => setPveAiDifficulty(e.target.value)}>
                                        <option value="EASY">Easy</option>
                                        <option value="MEDIUM">Medium</option>
                                        <option value="HARD">Hard</option>
                                    </Select>
                                </VStack>
                            )}
                            {createGameMode === 'AVA' && ( /* ... AVA Difficulty Selects ... */
                                <VStack spacing={4} align="stretch" w="100%">
                                    <VStack spacing={1} align="stretch">
                                        <Text fontSize="sm" color="gray.600">AI 1 (Plays as X):</Text>
                                        <Select value={avaAi1Difficulty} onChange={(e) => setAvaAi1Difficulty(e.target.value)}>
                                            <option value="EASY">Easy</option><option value="MEDIUM">Medium</option><option value="HARD">Hard</option>
                                        </Select>
                                    </VStack>
                                    <VStack spacing={1} align="stretch">
                                        <Text fontSize="sm" color="gray.600">AI 2 (Plays as O):</Text>
                                        <Select value={avaAi2Difficulty} onChange={(e) => setAvaAi2Difficulty(e.target.value)}>
                                            <option value="EASY">Easy</option><option value="MEDIUM">Medium</option><option value="HARD">Hard</option>
                                        </Select>
                                    </VStack>
                                </VStack>
                            )}

                            <Button colorScheme="teal" onClick={handleCreateGame} isLoading={isLoading && tabIndex === 0} width={"100%"} >
                                Create Game
                            </Button>
            </VStack>
                    </TabPanel>
                    <TabPanel p={0}> {/* Join Game Panel */}
                        <VStack spacing={6}>
                            <Heading as="h2" size="lg" textAlign="center">Join PvP Game</Heading>
                            <FormControl isRequired>
                                <FormLabel htmlFor="join-game-id">Game ID</FormLabel>
                                <Input
                                    id="join-game-id"
                                    placeholder="Enter Game ID from Player 1"
                                    value={joinGameId}
                                    onChange={(e) => setJoinGameId(e.target.value)}
                                />
                            </FormControl>
                            <Button colorScheme="blue" onClick={handleJoinGame} isLoading={isLoading && tabIndex === 1} width={"100%"} >
                                Join Game
                            </Button>
                        </VStack>
                    </TabPanel>
                </TabPanels>
            </Tabs>
        </Box>
    );
};

export default GameSetup;