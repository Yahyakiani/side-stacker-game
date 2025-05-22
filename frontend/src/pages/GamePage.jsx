// frontend/src/pages/GamePage.jsx
import React from 'react';
import { useToast } from '@chakra-ui/react'; // Keep useToast if specific toasts are still needed here

// Custom Hooks
import useGameWebSocket from '../hooks/useGameWebSocket';
import useGameStateManager from '../hooks/useGameStateManager'; // Assuming this hook also provides clientId or takes it

// View Components
import ConnectingToServerView from '../components/views/ConnectingToServerView';
import ConnectionErrorView from '../components/views/ConnectionErrorView';
import WaitingForOpponentView from '../components/views/WaitingForOpponentView';
import MainGamePlayView from '../components/views/MainGamePlayView';
import DefaultLoadingView from '../components/views/DefaultLoadingView';
import GameSetup from '../components/GameSetup'; // GameSetup is a distinct phase

// Constants
const GAME_STATUS = {
    SETUP: 'setup',
    WAITING: 'waiting',
    // WAITING_FOR_PLAYER2: 'waiting_for_player2', // This specific status might be consolidated into 'waiting'
    ACTIVE: 'active',
    // Define 'over' statuses more generically or check based on absence of other states
};

const GamePage = () => {
    const toast = useToast(); // If GamePage itself needs to show toasts not handled by hooks/views

    // Initialize game state and WebSocket handlers from custom hooks
    // If useGameStateManager needs clientId, and useGameWebSocket provides it:
    // const { clientId } = useGameWebSocket(...); // Simplified, assuming it returns clientId directly
    // const gameStateManager = useGameStateManager(clientId);
    // For now, let's assume useGameStateManager handles clientId internally or gets it via getClientId()
    const gameStateManager = useGameStateManager(); // Assuming it uses getClientId() internally if needed

    const {
        gameData,
        gameState,
        isLoading, // General loading (e.g., for setup)
        error: gameLogicError, // Errors from game logic/state updates
        setIsLoading,
        setError,
        resetGame,
        handleGameCreatedOrJoined,
        handleGameStart,
        handleGameUpdate,
        handleGameOver,
        handleWaitingForPlayer,
        handleExternalError, // For socket errors or other external errors
    } = gameStateManager;

    const {
        socketConnected,
        socketError, // Specific errors from WebSocket connection/protocol
        makeMove: sendMakeMoveViaWebSocket,
        // clientId // Available if needed directly in GamePage
    } = useGameWebSocket(
        handleGameCreatedOrJoined,
        handleGameStart,
        handleGameUpdate,
        handleGameOver,
        handleWaitingForPlayer,
        (errMsg) => { // Handler for errors from useGameWebSocket
            handleExternalError(errMsg); // Centralize error state management
    // Toast for connection error might be redundant if ConnectionErrorView handles it well
    // toast({ title: "Connection Error", description: errMsg, status: "error", duration: 5000, isClosable: true });
        }
        );

    const handleMakeMove = (rowIndex, side) => {
        if (!gameData || !gameData.game_id || !gameData.player_token) {
            handleExternalError("Game or player information is missing. Cannot make a move.");
            return;
        }
        if (gameState.current_player_token !== gameData.player_token) {
            toast({ title: "Not your turn!", status: "warning", duration: 2000, isClosable: true });
            return;
        }
        if (gameState.status !== GAME_STATUS.ACTIVE) {
            toast({ title: "Game is not active!", status: "warning", duration: 2000, isClosable: true });
            return;
        }
        sendMakeMoveViaWebSocket(gameData.game_id, gameData.player_token, rowIndex, side);
    };

    // Derived state for UI (can be passed to MainGamePlayView)
    const currentPlayerPieceForControls = gameData?.player_piece || '?';
    const isMyTurn = gameData && gameState.current_player_token === gameData.player_token;
    // isLoading here refers to general loading (e.g. during game setup).
    // MainGamePlayView might have its own internal loading state for move processing if needed,
    // or we pass a specific `isMoveProcessing` prop. For now, `isLoading` from gameStateManager.
    const controlsDisabled = !isMyTurn || gameState.status !== GAME_STATUS.ACTIVE || isLoading;


    // --- Conditional Rendering Logic ---
    const combinedError = gameLogicError || socketError;

    if (!socketConnected && !combinedError) {
        return <ConnectingToServerView />;
    }

    // Show critical connection or early game error
    // This condition means: if there's an error AND (either we are not connected OR gameData isn't set yet)
    if (combinedError && (!socketConnected || !gameData)) {
        return <ConnectionErrorView errorMessage={combinedError} />;
    }

    // Game Setup Phase
    if (!gameData || gameState.status === GAME_STATUS.SETUP) {
        return (
            <GameSetup
                isLoading={isLoading}
                setIsLoading={setIsLoading}
                setError={(msg) => handleExternalError(msg)} // Pass down the centralized error setter
            // Pass down 'gameLogicError' if GameSetup needs to display it directly for setup failures
            // error={gameLogicError}
            />
        );
        // Note: If GameSetup itself has errors, it should ideally display them,
        // or setError will update 'gameLogicError' which might trigger ConnectionErrorView if socket isn't connected.
    }

    // Waiting for Opponent Phase (after Player 1 created a PvP game)
    if (gameData && gameState.status === GAME_STATUS.WAITING) {
        // The 'waiting_for_player2' status might be specific or just 'waiting'.
        // Ensure your useGameStateManager hook sets status to 'waiting' correctly.
        return <WaitingForOpponentView gameId={gameData.game_id} />;
    }

    // Active Game or Game Over Phase
    // Check if gameState and gameData are sufficiently populated for main play
    if (gameData && (gameState.status === GAME_STATUS.ACTIVE || gameState.status.includes('wins') || gameState.status === 'draw')) {
        return (
            <MainGamePlayView
                gameData={gameData}
                gameState={gameState}
                onMakeMove={handleMakeMove}
                controlsDisabled={controlsDisabled}
                currentPlayerPiece={currentPlayerPieceForControls}
                isLoading={isLoading} // This isLoading is from gameStateManager, primarily for setup.
                // If moves have their own loading, that needs to be distinct.
                error={gameLogicError} // Errors specific to game logic after connection
                onResetGame={resetGame}
            />
        );
    }

    // Fallback / Default Loading State if none of the above match
    // This could indicate a transient state or an unhandled scenario.
    console.warn("GamePage: Reached fallback rendering state.", { gameData, gameState, socketConnected, combinedError });
    return <DefaultLoadingView message="Figuring out what to show..." />;
};

export default GamePage;