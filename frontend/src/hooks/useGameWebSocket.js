// src/hooks/useGameWebSocket.js (New File)
import { useState, useEffect, useCallback }
    from 'react';
import {
    connectWebSocket,
    getClientId,
    getSocket,
    makeMove as sendMakeMoveWebSocket,
    // Potentially createGame, joinGame if you want to abstract them further
    // from GameSetup, but for now, let's keep them in socketService.js direct calls
} from '../services/socketService';
import { WS_MSG_TYPES } from '../constants/gameConstants'; // Assuming you have a constants file for message types


const useGameWebSocket = (
    onGameCreatedOrJoined, // Callback for GAME_CREATED/JOINED
    onGameStart,           // Callback for GAME_START
    onGameUpdate,          // Callback for GAME_UPDATE
    onGameOver,            // Callback for GAME_OVER
    onWaitingForPlayer,    // Callback for WAITING_FOR_PLAYER
    onSocketError          // Callback for general socket errors/ERROR messages
) => {
    const [socketConnected, setSocketConnected] = useState(false);
    const [socketError, setSocketError] = useState(null); // Separate error state for socket

    const handleMainWebSocketMessage = useCallback((message) => {
        console.log("useGameWebSocket: Received WS message:", message);
        switch (message.type) {
            // GAME_CREATED and GAME_JOINED are handled by the specific callback in socketService
            // which calls onGameCreatedOrJoined directly.
            case WS_MSG_TYPES.GAME_START:
                onGameStart(message.payload);
                break;
            case WS_MSG_TYPES.GAME_UPDATE:
                onGameUpdate(message.payload);
                break;
            case WS_MSG_TYPES.GAME_OVER:
                onGameOver(message.payload);
                break;
            case WS_MSG_TYPES.ERROR:
                onSocketError(message.payload.message || "Unknown server error message.");
                break;
            case WS_MSG_TYPES.WAITING_FOR_PLAYER:
                onWaitingForPlayer(message.payload);
                break;
            default:
                console.warn("useGameWebSocket: Unhandled WebSocket message type:", message.type);
        }
    }, [onGameStart, onGameUpdate, onGameOver, onSocketError, onWaitingForPlayer]);

    const handleSpecificError = useCallback((errorMessage) => {
        console.error("useGameWebSocket: WebSocket Connection/Protocol Error:", errorMessage);
        setSocketError(errorMessage);
        setSocketConnected(false);
        if (onSocketError) { // Also notify the main component
            onSocketError(errorMessage);
        }
    }, [onSocketError]);

    useEffect(() => {
        console.log("useGameWebSocket: Attempting to connect...");
        connectWebSocket(
            handleMainWebSocketMessage,
            onGameCreatedOrJoined, // This is the callback from GamePage
            handleSpecificError
        );

        const intervalId = setInterval(() => {
            const sock = getSocket();
            setSocketConnected(sock && sock.readyState === WebSocket.OPEN);
        }, 1000);

        return () => {
            clearInterval(intervalId);
            const sock = getSocket();
            if (sock) {
                console.log("useGameWebSocket: Closing WebSocket connection on component unmount.");
                // Consider if socket.close() should be called here or handled by browser/socketService
            }
        };
    }, [handleMainWebSocketMessage, onGameCreatedOrJoined, handleSpecificError]); // Dependencies for connectWebSocket

    const makeMove = useCallback((gameId, playerToken, rowIndex, side) => {
        // Add pre-condition checks here if they are purely socket related,
        // or keep them in GamePage if they depend on gameData/gameState.
        // For now, keeping them in GamePage seems fine as they use gameData.
        sendMakeMoveWebSocket(gameId, playerToken, rowIndex, side);
    }, []);

    return {
        socketConnected,
        socketError, // Expose socket-specific error
        makeMove,
        clientId: getClientId(), // Expose client ID if needed elsewhere
    };
};

export default useGameWebSocket;