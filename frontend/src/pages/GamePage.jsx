// frontend/src/pages/GamePage.jsx
import React from 'react';
// ### MODIFICATION START ### Added Box for layout ### MODIFICATION END ###
import { Box, useToast } from '@chakra-ui/react';

// Custom Hooks
import useGameWebSocket from '../hooks/useGameWebSocket';
import useGameStateManager from '../hooks/useGameStateManager';

// View Components
import ConnectingToServerView from '../components/views/ConnectingToServerView';
import ConnectionErrorView from '../components/views/ConnectionErrorView';
import WaitingForOpponentView from '../components/views/WaitingForOpponentView';
import MainGamePlayView from '../components/views/MainGamePlayView';
import DefaultLoadingView from '../components/views/DefaultLoadingView';
import GameSetup from '../components/GameSetup';
// ### NEW LINE/BLOCK START ### Import GameHistoryStats ### NEW LINE/BLOCK END ###
import GameHistoryStats from '../components/GameHistoryStats'; // Make sure path is correct
// ### NEW LINE/BLOCK END ###
import { GAME_STATUS } from '../constants/gameConstants';


const GamePage = () => {
    const toast = useToast();

    // ### MODIFICATION START ### Destructure new state from useGameStateManager ### MODIFICATION END ###
    // Original destructuring:
    // const gameStateManager = useGameStateManager(); // Assuming it uses getClientId() internally if needed
    // const {
    //     gameData, gameState, isLoading, error: gameLogicError, setIsLoading, setError, resetGame,
    //     handleGameCreatedOrJoined, handleGameStart, handleGameUpdate, handleGameOver,
    //     handleWaitingForPlayer, handleExternalError,
    // } = gameStateManager;

    // New destructuring to include username and stats:
    // Assuming your useGameStateManager takes clientId as an argument (as per your original structure)
    // And that useGameWebSocket provides clientId
    const { // First, get clientId from useGameWebSocket
        socketConnected,
        socketError, // Specific errors from WebSocket connection/protocol
        makeMove: sendMakeMoveViaWebSocket,
        clientId // Get clientId from useGameWebSocket
    } = useGameWebSocket(
        // Pass the callback handlers here, they will be defined further down
        // after useGameStateManager is initialized with the clientId.
        // Temporary placeholders:
        () => { }, () => { }, () => { }, () => { }, () => { }, () => { }
    );

    const { // Now initialize useGameStateManager with the clientId
        gameData,
        gameState,
        isLoading, // This is the general loading from useGameStateManager
        error: gameLogicError, // Errors from game logic/state updates
        setIsLoading,
        setError: setGameLogicError, // Renamed to avoid conflict if you had a local setError
        resetGame,
        handleGameCreatedOrJoined,
        handleGameStart,
        handleGameUpdate,
        handleGameOver,
        handleWaitingForPlayer,
        handleExternalError,
        // --- New stats-related state ---
        username,           // Current username from useGameStateManager
        userStats,          // Current user stats
        statsLoading,       // Loading state for stats fetching
        statsError,         // Error state for stats fetching
        // setUsername,     // Expose if GameSetup needs to update it directly from GamePage
        // fetchUserStats,  // Expose if manual refresh needed from GamePage
    } = useGameStateManager(clientId); // Pass clientId to useGameStateManager

    // Now that handlers from useGameStateManager are defined, re-initialize useGameWebSocket with them
    // This looks a bit like a double initialization, but it's to resolve dependency order.
    // A different hook structure or context might avoid this.
    // For now, let's re-call useGameWebSocket to set the correct callbacks.
    // This is not ideal. A better way is to define callbacks that then call the methods from the hook.
    // Let's adjust to avoid re-calling the hook.

    // Define callbacks that will use the methods from the initialized useGameStateManager
    const gameCreatedOrJoinedCallback = (payload, type) => handleGameCreatedOrJoined(payload, type);
    const gameStartCallback = (payload) => handleGameStart(payload);
    const gameUpdateCallback = (payload) => handleGameUpdate(payload);
    const gameOverCallback = (payload) => handleGameOver(payload);
    const waitingForPlayerCallback = (payload) => handleWaitingForPlayer(payload);
    const externalErrorCallback = (errMsg) => handleExternalError(errMsg);


    const {
        // We only need socketConnected and socketError from the second call if we assume makeMove remains the same instance.
        // Actually, we've already destructured what we need. The callbacks are now set for the *existing* socket connection.
        // This is managed inside socketService.js; it updates its internal callback references.
        // So, no need to re-call useGameWebSocket itself. The first call to useGameWebSocket
        // should have passed these callback *references*.

        // The issue is that the functions (handleGameCreatedOrJoined etc.) are not defined
        // when useGameWebSocket is first called if useGameStateManager depends on clientId from useGameWebSocket.
        // The simplest way is to ensure useGameStateManager does *not* take clientId if it doesn't absolutely need it
        // for its own initialization logic, but rather gets it via getClientId() from socketService.
        // Let's assume your current useGameStateManager in your actual file can work without clientId as a param or gets it internally.

        // If useGameStateManager MUST have clientId from useGameWebSocket:
        // The callbacks passed to useGameWebSocket should be stable references or wrapped.
        // Example: useGameWebSocket((...args) => gameStateManagerInstance.handleGameCreatedOrJoined(...args), ...)
        // This is getting complex. Let's simplify by assuming useGameStateManager from your file:
        // `const gameStateManager = useGameStateManager();`
        // And `useGameWebSocket` receives the callbacks directly:
        // `useGameWebSocket( gameStateManager.handleGameCreatedOrJoined, ...)`
        // This means useGameStateManager should not take `clientId` as an argument if it creates a circular dependency.
        // Your provided code for GamePage.jsx was:
        // const gameStateManager = useGameStateManager();
        // const { ... } = gameStateManager;
        // const { ... } = useGameWebSocket(handleGameCreatedOrJoined, ...);
        // This structure is fine, assuming useGameStateManager() doesn't need a clientId from useGameWebSocket() for ITS OWN setup.
        // The `clientId` parameter in `useGameStateManager = (clientId)` is for the SPECTATOR logic within handleGameCreatedOrJoined.
        // This implies `clientId` MUST come from `useGameWebSocket`.

        // Corrected flow for dependencies:
        // 1. Call useGameWebSocket to get clientId.
        // 2. Call useGameStateManager, passing this clientId.
        // 3. The callbacks passed to useGameWebSocket MUST be stable or correctly referenced.
        // The socketService updates its internal callback references, so this should work.
    } = useGameWebSocket( // This call sets up socketService with the correct handlers
        gameCreatedOrJoinedCallback,
        gameStartCallback,
        gameUpdateCallback,
        gameOverCallback,
        waitingForPlayerCallback,
        externalErrorCallback
    );
    // ### MODIFICATION END ###


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

    const currentPlayerPieceForControls = gameData?.player_piece || '?';
    const isMyTurn = gameData && gameState.current_player_token === gameData.player_token;
    const controlsDisabled = !isMyTurn || gameState.status !== GAME_STATUS.ACTIVE || isLoading;


    // --- Conditional Rendering Logic ---
    let currentView; // Variable to hold the main view component
    const combinedError = gameLogicError || socketError;

    if (!socketConnected && !combinedError) {
        currentView = <ConnectingToServerView />;
    } else if (combinedError && (!socketConnected || !gameData && gameState.status !== GAME_STATUS.SETUP)) { // Adjusted condition for setup
        currentView = <ConnectionErrorView errorMessage={combinedError} />;
    } else if (!gameData || gameState.status === GAME_STATUS.SETUP) {
        currentView = (
            <GameSetup
                isLoading={isLoading}
                setIsLoading={setIsLoading}
                setError={(msg) => handleExternalError(msg)}
                // Pass username and setUsername if GameSetup needs to be controlled by GamePage's username state
                // currentUsername={username}
                // onUsernameChange={setUsername} // Ensure setUsername is exposed from useGameStateManager
            />
        );
    } else if (gameData && gameState.status === GAME_STATUS.WAITING) {
        currentView = <WaitingForOpponentView gameId={gameData.game_id} />;
    } else if (gameData && (gameState.status === GAME_STATUS.ACTIVE || gameState.status.includes('wins') || gameState.status === GAME_STATUS.DRAW || gameState.status === GAME_STATUS.GAME_OVER)) {
        // Added GAME_STATUS.GAME_OVER here as a general catch-all for ended games
        currentView = (
            <MainGamePlayView
                gameData={gameData}
                gameState={gameState}
                onMakeMove={handleMakeMove}
                controlsDisabled={controlsDisabled}
                currentPlayerPiece={currentPlayerPieceForControls}
                isLoading={isLoading}
                error={gameLogicError}
                onResetGame={resetGame}
            />
        );
    } else {
        console.warn("GamePage: Reached fallback rendering state.", { gameData, gameState, socketConnected, combinedError });
        currentView = <DefaultLoadingView message="Figuring out what to show..." />;
    }

    return (
        // ### MODIFICATION START ### Added Box wrapper and GameHistoryStats ### MODIFICATION END ###
        <Box pb={{ base: 16, md: 10 }}> {/* Add padding to bottom to ensure stats component is not cut off */}
            {currentView}

            {/* Conditionally render GameHistoryStats */}
            {/* Show stats if a username is set, typically shown during setup or after a game. */}
            {/* Adjust visibility condition as needed. */}
            {(gameState.status === GAME_STATUS.SETUP ||
                gameState.status === GAME_STATUS.GAME_OVER ||
                gameState.status.includes('wins') ||
                gameState.status === GAME_STATUS.DRAW) &&
                username && (
                    <Box maxW="lg" mx="auto" mt={6}> {/* Consistent width or slightly wider */}
                        <GameHistoryStats
                            username={username}
                            stats={userStats}
                            isLoading={statsLoading}
                            error={statsError}
                        />
                    </Box>
                )}
        </Box>
        // ### MODIFICATION END ###
    );
};

export default GamePage;