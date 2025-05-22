// src/components/views/MainGamePlayView.jsx
import React from 'react';
import { Container, VStack, Heading, Text, Spinner, Button } from '@chakra-ui/react';
import GameInfo from '../GameInfo'; // Assuming GameInfo is in ../components/
import Board from '../board/Board';   // Assuming Board is in ../components/board/
import Controls from '../Controls'; // Assuming Controls is in ../components/

// Make sure GAME_STATUS is accessible here or passed as props if needed for complex logic
// For simplicity, we'll rely on the parent (GamePage) to decide when to show this view.
const GAME_STATUS_ACTIVE = 'active'; // Or import from a shared constants file

const MainGamePlayView = ({
    gameData,
    gameState,
    onMakeMove,
    controlsDisabled,
    currentPlayerPiece,
    isLoading, // For in-game actions like processing a move
    error,     // For errors occurring during active gameplay
    onResetGame
}) => {
    const isGameActive = gameState.status === GAME_STATUS_ACTIVE;
    const isGameOver = !isGameActive && gameState.status !== 'setup' && gameState.status !== 'waiting'; // Simplified game over check

    return (
        <Container maxW="container.md" py={6}>
            <VStack spacing={6} align="stretch">
                <Heading as="h1" size="xl" textAlign="center" color="teal.600" mb={2}>
                    Side-Stacker
                </Heading>

                <GameInfo gameData={gameData} gameState={gameState} />
                <Board boardData={gameState.board} lastMove={gameState.last_move} />

                {isGameActive && gameData?.game_mode && !gameData.game_mode.startsWith('AVA') && (
                    <Controls
                        onMakeMove={onMakeMove}
                        isDisabled={controlsDisabled}
                        currentPlayerPiece={currentPlayerPiece}
                    />
                )}

                {isLoading && isGameActive && // Show spinner only during active game processing
                    <Spinner
                        label="Processing..."
                        thickness="4px"
                        speed="0.65s"
                        emptyColor="gray.200"
                        color="blue.500"
                        size="xl"
                        mt={4} // Added margin for better spacing
                    />
                }
                {error && !isLoading && // Display general game errors
                    <Text color="red.500" mt={2} textAlign="center">
                        Error: {error}
                    </Text>
                }

                {isGameOver && (
                    <Button
                        onClick={onResetGame}
                        colorScheme="pink"
                        size="lg"
                        mt={4}
                    >
                        {gameData?.game_mode?.startsWith('AVA') ? "Spectate New AI Game" : "Play Again (New Game)"}
                    </Button>
                )}
            </VStack>
        </Container>
    );
};

export default MainGamePlayView;