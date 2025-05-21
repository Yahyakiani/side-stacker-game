// frontend/src/services/socketService.js

let socket = null
let onMessageCallback = null // To allow components to register a message handler
let onGameCreatedCallback = null // Specific callback for game creation
let onErrorCallback = null // Specific callback for errors
let onGameJoinedCallback = null;  // For GAME_JOINED (if we want a separate one)

const VITE_WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/v1/ws-game/ws'

const generateClientId = () => {
    // Simple UUID v4 generator
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
    })
}

const clientId = generateClientId() // Generate a unique ID for this client session
export const getClientId = () => clientId;

export const connectWebSocket = (
    generalMessageCb,
    gameCreatedCb, // Specifically for GAME_CREATED from GamePage
    // gameJoinedCb, // If you want a separate one for GAME_JOINED
    errorCb
) => {
    // Always update callbacks to the latest ones from the calling component
    onMessageCallback = generalMessageCb;
    onGameCreatedCallback = gameCreatedCb;
    // onGameJoinedCallback = gameJoinedCb;
    onErrorCallback = errorCb;

    if (socket && socket.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected. Callbacks updated.');
        return socket;
    }
    if (socket && socket.readyState === WebSocket.CONNECTING) {
        console.log('WebSocket is currently connecting. Callbacks updated.');
        return socket;
    }

    const wsUrl = `${VITE_WS_BASE_URL}/${getClientId()}`; // Use getClientId()
    console.log('Attempting to connect WebSocket to:', wsUrl);
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('WebSocket connected successfully!');
        if (typeof setSocketConnected === 'function') setSocketConnected(true); // If GamePage passes this
    };

    socket.onmessage = (event) => {
        console.log('WebSocket message received:', event.data);
        try {
          const message = JSON.parse(event.data);

          if (onMessageCallback) { // General handler in GamePage
              onMessageCallback(message);
          }

          // Specific callback handling (can be redundant if general handler covers it, but explicit)
          if (message.type === "GAME_CREATED" && onGameCreatedCallback) {
            onGameCreatedCallback(message.payload); // This is handleGameCreatedOrJoined in GamePage
        }

        else if (message.type === "ERROR" && onErrorCallback) {
            onErrorCallback(message.payload.message || 'Unknown server error');
        }
      } catch (error) {
          console.error('Error parsing WebSocket message or in callback:', error);
          if (onErrorCallback) onErrorCallback('Failed to process message from server.');
      }
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (onErrorCallback) {
            onErrorCallback('WebSocket connection error.')
        }
        // Potentially try to reconnect here or notify user
    }

    socket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.reason, `Code: ${event.code}`)
        socket = null // Clear the socket instance
        if (onErrorCallback) {
            onErrorCallback(`WebSocket disconnected: ${event.reason || 'Connection closed'}`)
        }
        // Potentially try to reconnect here or notify user
    }
    return socket
}

export const sendMessage = (message) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        console.log('Sending WebSocket message:', message)
        socket.send(JSON.stringify(message))
    } else {
        console.error('WebSocket is not connected. Cannot send message.')
        if (onErrorCallback) {
            onErrorCallback('Cannot send message: WebSocket not connected.')
        }
    }
}

export const createGame = (mode = 'PVP', options = {}) => {
    // mode: "PVP", "PVE", "AVA"
    // options: for PVE -> "EASY" (string for difficulty)
    //          for AVA -> { ai1_difficulty: "EASY", ai2_difficulty: "MEDIUM" } (object)
    //          for PVP -> {} (empty object or undefined)

    const payload = {
        player_temp_id: clientId,
        mode: mode.toUpperCase(),
    };

    if (mode.toUpperCase() === 'PVE') {
        if (typeof options === 'string') { // options is the difficulty string
            payload.difficulty = options.toUpperCase();
        } else {
            console.error("PVE mode selected but difficulty string not provided correctly in options.");
            // Handle error or default
            payload.difficulty = "EASY"; // Default if incorrect
    }
    } else if (mode.toUpperCase() === 'AVA') {
        if (typeof options === 'object' && options !== null) {
            if (options.ai1_difficulty) payload.ai1_difficulty = options.ai1_difficulty.toUpperCase();
            if (options.ai2_difficulty) payload.ai2_difficulty = options.ai2_difficulty.toUpperCase();
        } else {
            console.error("AVA mode selected but AI difficulties object not provided correctly in options.");
            // Handle error or default
            payload.ai1_difficulty = "EASY";
            payload.ai2_difficulty = "EASY";
        }
    }

    sendMessage({ type: "CREATE_GAME", payload });
};

export const getSocket = () => socket // To allow components to check socket state if needed

export const makeMove = (gameId, playerToken, row, side) => {
    if (!gameId || !playerToken) {
        console.error("makeMove: gameId and playerToken are required.")
        // Optionally call onErrorCallback if it's set
        return;
    }
    const payload = {
        game_id: gameId, // Though game_id is implicit in the server's room management, sending it is fine
        player_token: playerToken,
        row: parseInt(row, 10), // Ensure row is an integer
        side: side.toUpperCase()
    }
    sendMessage({ type: "MAKE_MOVE", payload })
}
// No disconnect function exposed directly for now, relies on browser closing or server.
// Could add one if manual disconnect from UI is needed.
// export const disconnectWebSocket = () => {
//   if (socket) {
//     socket.close()
//   }
// }