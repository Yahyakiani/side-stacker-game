// frontend/src/services/socketService.js

import { WS_MSG_TYPES, AI_DIFFICULTY, GAME_MODES, USERNAME_PAYLOAD_KEY } from '../constants/gameConstants';

// --- Constants ---
const DEFAULT_WS_BASE_URL = 'ws://localhost:8000/api/v1/ws-game/ws';
const VITE_WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || DEFAULT_WS_BASE_URL;

// --- Module-level State ---
let socketInstance = null; // Renamed for clarity to distinguish from a local 'socket' variable
let onGeneralMessage = null;
let onGameSetupSuccess = null; // Renamed for better semantic meaning (handles GAME_CREATED & GAME_JOINED)
let onConnectionError = null;

// --- Client ID Generation and Management ---
const generateClientId = () => {
    // Simple UUID v4 generator
    // Ref: https://stackoverflow.com/a/2117523/123456
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
};

// Generate a unique ID for this client session only once per module load.
const currentClientId = generateClientId();
export const getClientId = () => currentClientId;

// --- WebSocket Connection Management ---
export const connectWebSocket = (
    generalMessageCallback,
    gameSetupSuccessCallback, // For GAME_CREATED and GAME_JOINED success
    connectionErrorCallback
) => {
    // Update registered callbacks to the latest ones from the calling component (e.g., useGameWebSocket hook)
    onGeneralMessage = generalMessageCallback;
    onGameSetupSuccess = gameSetupSuccessCallback;
    onConnectionError = connectionErrorCallback;

    if (socketInstance && socketInstance.readyState === WebSocket.OPEN) {
        console.log('socketService: WebSocket already connected. Callbacks updated.');
        return socketInstance;
    }
    if (socketInstance && socketInstance.readyState === WebSocket.CONNECTING) {
        console.log('socketService: WebSocket is currently connecting. Callbacks updated.');
        return socketInstance;
    }

    const wsUrl = `${VITE_WS_BASE_URL}/${getClientId()}`;
    console.log('socketService: Attempting to connect WebSocket to:', wsUrl);
    socketInstance = new WebSocket(wsUrl);

    socketInstance.onopen = () => {
        console.log('socketService: WebSocket connected successfully!');
    // The `setSocketConnected` function call was specific to an older GamePage implementation.
    // The `useGameWebSocket` hook now manages its own `socketConnected` state based on `getSocket()`.
    };

    socketInstance.onmessage = (event) => {
        console.log('socketService: WebSocket message received:', event.data);
        try {
            const message = JSON.parse(event.data);

            // Prioritize specific handlers if they exist
            if (
                (message.type === WS_MSG_TYPES.GAME_CREATED || message.type === WS_MSG_TYPES.GAME_JOINED) &&
                onGameSetupSuccess
            ) {
                onGameSetupSuccess(message.payload, message.type); // Pass type for context
            }

            // Always call the general message handler if provided.
            // The general handler (in useGameWebSocket) can decide to ignore messages
            // already handled by specific callbacks if necessary.
            if (onGeneralMessage) {
                onGeneralMessage(message);
            }

            // Specific handling for top-level ERROR messages directly from the server,
            // if not intended to be routed through the general message handler first.
            // This is somewhat redundant if the general handler in useGameWebSocket also processes "ERROR".
            // If onGeneralMessage handles "ERROR", this block might be removed or conditioned.
            if (message.type === WS_MSG_TYPES.ERROR && onConnectionError && !onGeneralMessage) {
                // Only if onGeneralMessage isn't defined, otherwise let it handle ERROR.
                onConnectionError(message.payload?.message || 'Unknown server error');
            }

        } catch (error) {
            console.error('socketService: Error parsing WebSocket message or in callback:', error);
            if (onConnectionError) {
                onConnectionError('Failed to process message from server.');
            }
        }
    };

    socketInstance.onerror = (errorEvent) => {
        // The 'error' event object itself might not be very descriptive.
        // It's often followed by an 'onclose' event with more details.
        console.error('socketService: WebSocket error occurred.', errorEvent);
        if (onConnectionError) {
            onConnectionError('WebSocket connection error. See console for details.');
        }
        // Note: Reconnection logic could be initiated here if desired.
    };

    socketInstance.onclose = (event) => {
        console.log(`socketService: WebSocket disconnected. Reason: ${event.reason || 'N/A'}, Code: ${event.code}`);
        socketInstance = null; // Important to clear the instance for future reconnections
        if (onConnectionError) {
            onConnectionError(`WebSocket disconnected: ${event.reason || 'Connection closed'}`);
        }
        // Note: Reconnection logic could be initiated here if desired.
    };

    return socketInstance;
};

// --- Sending Messages ---
export const sendMessage = (messageObject) => {
    if (socketInstance && socketInstance.readyState === WebSocket.OPEN) {
        console.log('socketService: Sending WebSocket message:', messageObject);
        socketInstance.send(JSON.stringify(messageObject));
    } else {
        const errorMsg = 'socketService: WebSocket is not connected. Cannot send message.';
        console.error(errorMsg, messageObject);
        if (onConnectionError) { // Notify about the failure to send
            onConnectionError('Cannot send message: WebSocket not connected.');
        }
        // Optionally, throw an error here or return a status
        // throw new Error(errorMsg);
    }
};

// --- Game Action Senders ---
// These functions create and send specific message types.

export const createGame = (mode = GAME_MODES.PVP, options = {}, username = null) => {
    const upperCaseMode = mode.toUpperCase();
    const payload = {
        player_temp_id: getClientId(),
        mode: upperCaseMode,
    };

    if (username && (upperCaseMode === GAME_MODES.PVP || upperCaseMode === GAME_MODES.PVE)) { // Add username if provided and relevant mode
        payload[USERNAME_PAYLOAD_KEY] = username;
    }

    if (upperCaseMode === GAME_MODES.PVE) {
        if (typeof options === 'string' && options.trim() !== '') {
            payload.difficulty = options.toUpperCase();
        } else {
            console.warn("socketService: PVE mode - 'options' should be a non-empty difficulty string. Defaulting to EASY.");
            payload.difficulty = AI_DIFFICULTY.EASY; // Default to EASY if not provided
        }
    } else if (upperCaseMode === GAME_MODES.AVA) {
        if (typeof options === 'object' && options !== null) {
            if (options.ai1_difficulty) payload.ai1_difficulty = options.ai1_difficulty.toUpperCase();
            else {
                console.warn("socketService: AVA mode - 'ai1_difficulty' missing in options. Defaulting to EASY.");
                payload.ai1_difficulty = AI_DIFFICULTY.EASY;
            }
            if (options.ai2_difficulty) payload.ai2_difficulty = options.ai2_difficulty.toUpperCase();
            else {
                console.warn("socketService: AVA mode - 'ai2_difficulty' missing in options. Defaulting to EASY.");
                payload.ai2_difficulty = AI_DIFFICULTY.EASY;
            }
        } else {
            console.warn("socketService: AVA mode - 'options' object for AI difficulties not provided correctly. Defaulting AI difficulties to EASY.");
            payload.ai1_difficulty = AI_DIFFICULTY.EASY;
            payload.ai2_difficulty = AI_DIFFICULTY.EASY;
        }
    }
    // No specific options needed for PVP from the frontend in this structure.

    sendMessage({ type: WS_MSG_TYPES.CREATE_GAME, payload });
};

export const joinGame = (gameIdToJoin, username = null) => {
    if (!gameIdToJoin || String(gameIdToJoin).trim() === '') {
        const errorMsg = "socketService: gameIdToJoin is required and cannot be empty for joinGame.";
        console.error(errorMsg);
        if (onConnectionError) onConnectionError("Game ID is required to join.");
        return;
    }
    const payload = {
        player_temp_id: getClientId(),
        game_id: String(gameIdToJoin).trim(),
    };

    if (username) { // Add username if provided
        payload[USERNAME_PAYLOAD_KEY] = username;
    }
    sendMessage({ type: WS_MSG_TYPES.JOIN_GAME, payload });
};

export const makeMove = (gameId, playerToken, row, side) => {
    if (!gameId || !playerToken) {
        console.error("socketService: gameId and playerToken are required for makeMove.");
        // Optionally call onConnectionError or throw, depending on desired error handling strategy
        return;
    }
    if (row === undefined || side === undefined || String(side).trim() === '') {
        console.error("socketService: row and side are required for makeMove.");
        return;
    }

    const payload = {
        game_id: gameId,
        player_token: playerToken,
        row: parseInt(row, 10), // Ensure row is an integer
        side: String(side).toUpperCase().trim(),
    };
    sendMessage({ type: WS_MSG_TYPES.MAKE_MOVE, payload });
};

// --- Utility ---
export const getSocket = () => socketInstance; // To allow components/hooks to check socket state

// --- Manual Disconnect (Optional) ---
// export const disconnectWebSocket = () => {
//   if (socketInstance && socketInstance.readyState === WebSocket.OPEN) {
//     console.log('socketService: Manually closing WebSocket connection.');
//     socketInstance.close(1000, "Client initiated disconnect"); // 1000 is normal closure
//   }
//   socketInstance = null; // Ensure it's cleared
// };