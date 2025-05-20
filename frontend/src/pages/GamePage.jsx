// frontend/src/pages/GamePage.jsx
import React, { useState, useEffect, useCallback } from 'react'
import { Box, VStack, Heading, Text, Spinner } from '@chakra-ui/react'
import GameSetup from '../components/GameSetup'
// import Board from '../components/board/Board'
import { connectWebSocket, sendMessage, getSocket } from '../services/socketService' // Import socket functions

const GamePage = () => {
    const [gameData, setGameData] = useState(null) // Stores game_id, player_token, player_piece
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState(null)
    const [socketConnected, setSocketConnected] = useState(false)

    // Callback for when GAME_CREATED message is received
    const handleGameCreated = useCallback((payload) => {
        console.log('GamePage: Game created/joined successfully:', payload)
        setGameData({
            game_id: payload.game_id,
            player_token: payload.player_token,
            player_piece: payload.player_piece,
            // initialMessage: payload.message // Optional: display initial message
        })
        setIsLoading(false)
        setError(null)
    }, [])

    // General message handler (can be expanded)
    const handleWebSocketMessage = useCallback((message) => {
        console.log("GamePage: Received general WS message:", message)
        // Handle other message types like GAME_UPDATE, GAME_OVER here
        if (message.type === "WAITING_FOR_PLAYER") {
            console.log("Game status: Waiting for P2")
            // You might want to update some UI state here
        }
    }, [])

    const handleWebSocketError = useCallback((errorMessage) => {
        console.error("GamePage: WebSocket Error:", errorMessage)
        setError(errorMessage)
        setIsLoading(false)
        setSocketConnected(false)
    }, [])

    // Effect to establish WebSocket connection on component mount
    useEffect(() => {
        console.log("GamePage: Attempting to connect WebSocket...")
        connectWebSocket(
            handleWebSocketMessage,
            handleGameCreated,
            handleWebSocketError
        )

        // Check connection status periodically or based on onopen/onclose
        const intervalId = setInterval(() => {
            const sock = getSocket()
            if (sock && sock.readyState === WebSocket.OPEN) {
                setSocketConnected(true)
            } else {
                setSocketConnected(false)
            }
        }, 1000)

        return () => {
            clearInterval(intervalId)
            const sock = getSocket()
            if (sock) {
                console.log("GamePage: Closing WebSocket connection on unmount.")
                // sock.close() // socketService's onclose will handle cleanup
            }
        }
    }, [handleWebSocketMessage, handleGameCreated, handleWebSocketError]) // Dependencies for useCallback

    if (!socketConnected && !error) {
        return (
            <Box textAlign="center" p={10}>
                <Spinner size="xl" />
                <Text mt={4}>Connecting to server...</Text>
            </Box>
        )
    }
    if (error && !gameData) { // Show error prominently if connection failed before game creation
        return (
            <Box textAlign="center" p={10}>
                <Heading color="red.500">Connection Error</Heading>
                <Text>{error}</Text>
                <Text mt={2}>Please ensure the backend server is running and try refreshing.</Text>
            </Box>
        )
    }

    // If WebSocket is connected but no gameData yet, show setup
    if (!gameData) {
        return (
            <GameSetup
                setIsLoading={setIsLoading} // GameSetup will use this to show its own loading state during API call
                setError={setError}         // GameSetup can set errors related to its own actions
            />
        )
    }

    // Once gameData is set, display game details
    return (
        <VStack spacing={4} align="stretch" p={5}>
            <Heading as="h1" size="lg" textAlign="center">
                Side-Stacker Game
            </Heading>
            <Text fontWeight="bold">Status: WebSocket Connected</Text>
            <Box p={3} borderWidth="1px" borderRadius="md" bg="blue.50">
                <Heading size="md">Game Details</Heading>
                <Text>Game ID: {gameData.game_id}</Text>
                <Text>Your Token: {gameData.player_token}</Text>
                <Text>Your Piece: {gameData.player_piece}</Text>
                {/* {gameData.initialMessage && <Text mt={2} fontStyle="italic">{gameData.initialMessage}</Text>} */}
            </Box>

            {/* Placeholder for Board, GameInfo, Controls */}
            <Box borderWidth="1px" borderRadius="lg" p={4}>
                <Text>Board Placeholder</Text>
            </Box>
            {/* ... other placeholders ... */}

            {isLoading && <Spinner />}
            {error && <Text color="red.500" mt={2}>Error: {error}</Text>}
        </VStack>
    )
}

export default GamePage