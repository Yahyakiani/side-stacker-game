// frontend/src/services/socketService.js

let socket = null
let onMessageCallback = null // To allow components to register a message handler
let onGameCreatedCallback = null // Specific callback for game creation
let onErrorCallback = null // Specific callback for errors

const VITE_WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/v1/ws-game/ws'

const generateClientId = () => {
    // Simple UUID v4 generator
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
    })
}

const clientId = generateClientId() // Generate a unique ID for this client session

export const connectWebSocket = (
    messageCallback, // General message handler
    gameCreatedCallback, // Specific for GAME_CREATED
    errorCallback      // Specific for ERROR
) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected.')
        return socket
    }

    const wsUrl = `${VITE_WS_BASE_URL}/${clientId}`
    console.log('Attempting to connect WebSocket to:', wsUrl)
    socket = new WebSocket(wsUrl)

    onMessageCallback = messageCallback
    onGameCreatedCallback = gameCreatedCallback
    onErrorCallback = errorCallback

    socket.onopen = () => {
        console.log('WebSocket connected successfully!')
        // You could send an initial "hello" message or client info if needed
        // sendMessage({ type: "CLIENT_HELLO", payload: { clientId } })
    }

    socket.onmessage = (event) => {
        console.log('WebSocket message received:', event.data)
        try {
            const message = JSON.parse(event.data)

            // General message handling
            if (onMessageCallback) {
                onMessageCallback(message)
            }

            // Specific handlers based on message type
            if (message.type === "GAME_CREATED" && onGameCreatedCallback) {
                onGameCreatedCallback(message.payload)
            } else if (message.type === "WAITING_FOR_PLAYER") {
                // Handle waiting for player (e.g., update UI)
                console.log("Game state: Waiting for another player.")
            } else if (message.type === "ERROR" && onErrorCallback) {
                onErrorCallback(message.payload.message || 'Unknown server error')
            }
            // Add more specific handlers here for GAME_UPDATE, GAME_OVER, etc.

        } catch (error) {
            console.error('Error parsing WebSocket message or in callback:', error)
            if (onErrorCallback) {
                onErrorCallback('Failed to process message from server.')
            }
        }
    }

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

export const createGame = (mode = 'PVP', aiDifficulty = null) => {
    // The player_temp_id can be the clientId or another identifier
    const payload = {
        player_temp_id: clientId, // Use the generated clientId for this session
        mode: mode.toUpperCase()
    }
    if (mode.toUpperCase().startsWith('PVE') && aiDifficulty) {
        payload.difficulty = aiDifficulty.toUpperCase()
    }
    sendMessage({ type: "CREATE_GAME", payload })
}

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