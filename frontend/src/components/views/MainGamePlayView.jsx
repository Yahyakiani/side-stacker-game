// src/components/views/MainGamePlayView.jsx
import React from 'react';
import { Container, VStack, Heading, Text, Spinner, Button, Icon, Box, HStack } from '@chakra-ui/react';
import GameInfo from '../GameInfo'; // Assuming GameInfo is in ../components/
import Board from '../board/Board';   // Assuming Board is in ../components/board/
import { GAME_STATUS, NUM_ROWS } from '../../constants/gameConstants'; // Adjust the import path as necessary
import { FaArrowLeft, FaArrowRight } from 'react-icons/fa'; // Added icons
// import Controls from '../Controls'; // Assuming Controls is in ../components/


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
    const isGameActive = gameState.status === GAME_STATUS.ACTIVE;
    const isGameOver = !isGameActive && gameState.status !== GAME_STATUS.SETUP && gameState.status !== GAME_STATUS.WAITING; // Simplified game over check


    const handleMoveButtonClick = (rowIndex, side) => {
        if (!controlsDisabled) {
            onMakeMove(rowIndex, side);
        }
    };

    // Helper to render a column of control buttons
    const renderControlColumn = (side) => {
        const isLeft = side === 'L';
        return (
            <VStack spacing={4} align={isLeft ? "flex-end" : "flex-start"} justifyContent="center" px={2} height="100%">
                {Array.from({ length: NUM_ROWS }).map((_, rowIndex) => (
                    <Button
                        key={`${side}-${rowIndex}`}
                        onClick={() => handleMoveButtonClick(rowIndex, side)}
                        isDisabled={controlsDisabled}
                        leftIcon={isLeft ? <Icon as={FaArrowLeft} /> : undefined}
                        rightIcon={!isLeft ? <Icon as={FaArrowRight} /> : undefined}
                        colorScheme={isLeft ? "green" : "blue"}
                        variant="outline"
                        size="sm" // Adjust size as needed
                        // Ensure button height + spacing roughly matches board row height for good alignment
                        // Chakra button default height for 'sm' is 32px. Board cell is 50px + 2px gap.
                        // We might need to adjust spacing or button height/padding.
                        // For now, let's keep it simple.
                        width="110px" // Fixed width for alignment
                        justifyContent={isLeft ? "flex-start" : "flex-end"} // Align text and icon
                        px={isLeft ? 3 : 2} // Adjust padding for icon alignment
                    >
                        {isLeft ? `Row ${rowIndex}` : `Row ${rowIndex}`}
                    </Button>
                ))}
            </VStack>
        );
    };


    return (
        <Container maxW="container.md" py={6}>
            <VStack spacing={7} align="stretch">
                <Heading as="h1" size="xl" textAlign="center" color="teal.600" mb={2}>
                    Side-Stacker
                </Heading>

                <GameInfo gameData={gameData} gameState={gameState} />
                {/* <Board boardData={gameState.board} lastMove={gameState.last_move} /> */}

                <HStack spacing={3} justifyContent="center" alignItems="center"> {/* Main layout for board and controls */}
                    {/* Left Controls - Render only if game is active and not AVA */}
                    {isGameActive && gameData?.game_mode && !gameData.game_mode.startsWith('AVA') ? (
                        renderControlColumn('L')
                    ) : (
                        <Box width="110px" px={2} /> // Placeholder for spacing if controls not shown
                    )}

                    <Board boardData={gameState.board} lastMove={gameState.last_move} />

                    {/* Right Controls - Render only if game is active and not AVA */}
                    {isGameActive && gameData?.game_mode && !gameData.game_mode.startsWith('AVA') ? (
                        renderControlColumn('R')
                    ) : (
                        <Box width="110px" px={2} /> // Placeholder for spacing if controls not shown
                    )}
                </HStack>

                {/* {isGameActive && gameData?.game_mode && !gameData.game_mode.startsWith('AVA') && (
                    <Controls
                        onMakeMove={onMakeMove}
                        isDisabled={controlsDisabled}
                        currentPlayerPiece={currentPlayerPiece}
                    />
                )} */}

                {isGameActive && gameData?.game_mode && !gameData.game_mode.startsWith('AVA') && !controlsDisabled && (
                    <Text textAlign="center" fontWeight="bold" fontSize="lg" mb={2}>
                        Click a side to place your piece ({currentPlayerPiece || '?'})
                    </Text>
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