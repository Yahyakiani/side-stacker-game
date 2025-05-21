// frontend/src/pages/GamePage.jsx
import React, { useState, useEffect, useCallback } from 'react'
import { Box, VStack, Heading, Text, Spinner, useToast, Button, Container } from '@chakra-ui/react'
import GameSetup from '../components/GameSetup'
import Board from '../components/board/Board' // Uncomment
import Controls from '../components/Controls'   // Import Controls
import GameInfo from '../components/GameInfo' // Will add later 
import { connectWebSocket, sendMessage, getSocket, makeMove as sendMakeMoveWebSocket } from '../services/socketService'

const GamePage = () => {
    // gameData will store: game_id, player_token (this client's), player_piece (this client's X or O)
    const [gameData, setGameData] = useState(null)

    // gameState will store: board, current_player_token (whose turn), status, winner_token, players_map ({token: piece})
    const [gameState, setGameState] = useState({
        board: Array(7).fill(Array(7).fill(null)), // Initial empty board for display
        current_player_token: null,
        status: 'setup', // 'setup', 'waiting', 'active', 'over'
        winner_token: null,
        players_map: {}, // e.g. { "player_one_token": "X", "player_two_token": "O" }
        last_move: null
    })

    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState(null)
    const [socketConnected, setSocketConnected] = useState(false)
    const toast = useToast() // For notifications

    const resetGameState = useCallback(() => {
        setGameData(null)
        setGameState({
            board: Array(7).fill(Array(7).fill(null)),
            current_player_token: null,
            status: 'setup',
            winner_token: null,
            players_map: {},
            last_move: null
        })
        setError(null)
        setIsLoading(false) // Ensure loading is also reset
    }, [])


    const handleGameCreatedOrJoined = useCallback((payload, type) => {
        console.log(`GamePage: ${type} success:`, payload)
        setGameData({
            game_id: payload.game_id,
            player_token: payload.player_token,
            player_piece: payload.player_piece,
        })
        if (type === "GAME_CREATED" && payload.message) {
            toast({ title: payload.message, status: "info", duration: 3000, isClosable: true })
        }
        if (type === "GAME_JOINED" && payload.message) {
            toast({ title: payload.message, status: "success", duration: 3000, isClosable: true })
        }
        // GAME_START will set the initial board and current player
        setIsLoading(false)
        setError(null)
    }, [toast])

    const handleGameStart = useCallback((payload) => {
        console.log("GamePage: GAME_START received", payload)
        setGameState(prevState => ({
            ...prevState,
            board: payload.board,
            current_player_token: payload.current_player_token,
            players_map: payload.players,
            status: 'active', // Game is now active
            winner_token: null, // Reset winner
            last_move: null
        }))
        // Update gameData if 'your_token' and 'your_piece' are in GAME_START and differ (e.g. on reconnect)
        if (payload.your_token && payload.your_piece && gameData?.player_token !== payload.your_token) {
            setGameData({
                game_id: payload.game_id,
                player_token: payload.your_token,
                player_piece: payload.your_piece
            })
        }
        toast({ title: "Game Started! It's " + (payload.players[payload.current_player_token] || 'Unknown') + "'s turn.", status: "success", duration: 3000, isClosable: true });
    }, [toast, gameData]) // gameData added to dependency array

    const handleWebSocketError = useCallback((errorMessage) => {
        console.error("GamePage: WebSocket Error:", errorMessage)
        setError(errorMessage)
        toast({ title: "Connection Error", description: errorMessage, status: "error", duration: 5000, isClosable: true })
        setIsLoading(false)
        setSocketConnected(false)
    }, [toast])

    const handleGameUpdate = useCallback((payload) => {
        console.log("GamePage: GAME_UPDATE received", payload)

        setGameState(prevState => {
            const updatedState = {
                ...prevState,
                board: payload.board,
                current_player_token: payload.current_player_token,
                last_move: payload.last_move,
                status: 'active'
            }

            const nextToken = payload.current_player_token
            const nextPiece = prevState.players_map[nextToken]
            if (nextToken) {
                toast({
                    title: "Move made. It's " + (nextPiece || 'Unknown') + "'s turn.",
                    status: "info",
                    duration: 2000,
                    isClosable: true
                })
            }

            return updatedState
        })
    }, [toast])

    const handleGameOver = useCallback((payload) => {
        console.log("GamePage: GAME_OVER received", payload)
        setGameState(prevState => ({
            ...prevState,
            board: payload.board,
            current_player_token: null, // No current player
            status: payload.status, // e.g., "player_x_wins", "draw"
            winner_token: payload.winner_token,
        }))
        let WinnerText = "Game Over!"
        if (payload.winner_token === "draw") {
            WinnerText = "It's a Draw!"
        } else if (payload.winner_token) {
            const winnerPiece = gameState.players_map[payload.winner_token] || payload.winning_player_piece
            WinnerText = `Player ${winnerPiece} Wins!`
        }
        toast({ title: WinnerText, status: payload.winner_token === "draw" ? "warning" : "success", duration: 5000, isClosable: true });
    }, [toast, gameState.players_map]) // Added gameState.players_map

    const handleWebSocketMessage = useCallback((message) => {
        console.log("GamePage: Received general WS message:", message)
        switch (message.type) {
            //   case "GAME_CREATED": // Handled by specific callback now
            //   case "GAME_JOINED":  // Handled by specific callback now
            //       // handleGameCreatedOrJoined(message.payload, message.type) // Not needed if specific callback used
            //       break
            case "GAME_START":
                handleGameStart(message.payload)
                break
            case "GAME_UPDATE":
                handleGameUpdate(message.payload)
                break
            case "GAME_OVER":
                handleGameOver(message.payload)
                break
            case "WAITING_FOR_PLAYER":
                toast({ title: "Waiting for opponent...", status: "info", duration: null, isClosable: true, id: "waiting-toast" })
                setGameState(prevState => ({ ...prevState, status: 'waiting' }))
                break
            case "ERROR": // General server error for this client
                handleWebSocketError(message.payload.message || "Unknown server error message.")
                break
            default:
                console.warn("GamePage: Unhandled WebSocket message type:", message.type)
        }
    }, [handleGameStart, handleGameUpdate, handleGameOver, toast, handleWebSocketError])



    useEffect(() => {
        console.log("GamePage: Attempting to connect WebSocket...")
        connectWebSocket(
            handleWebSocketMessage, 
            (payload) => handleGameCreatedOrJoined(payload, "GAME_CREATED"), // Pass type for GAME_CREATED
            handleWebSocketError
            // For GAME_JOINED, we'd need another way if a user joins via UI later.
            // For now, CREATE_GAME is the main entry point.
        )

        const intervalId = setInterval(() => {
            const sock = getSocket()
            setSocketConnected(sock && sock.readyState === WebSocket.OPEN)
        }, 1000)

        return () => {
            clearInterval(intervalId)
            const sock = getSocket()
            if (sock) {
                console.log("GamePage: Closing WebSocket connection on unmount.")
                // socket.close(); // Let browser handle or implement explicit disconnect in socketService
            }
        }
        // Ensure useCallback functions passed to connectWebSocket don't change unnecessarily often
    }, [handleWebSocketMessage, handleGameCreatedOrJoined, handleWebSocketError])


    const handleMakeMove = (rowIndex, side) => {
        if (!gameData || !gameData.game_id || !gameData.player_token) {
            setError("Game or player information is missing. Cannot make a move.")
            return
    }
        if (gameState.current_player_token !== gameData.player_token) {
            toast({ title: "Not your turn!", status: "warning", duration: 2000, isClosable: true })
            return
        }
        if (gameState.status !== 'active') {
            toast({ title: "Game is not active!", status: "warning", duration: 2000, isClosable: true })
            return
        }
        console.log(`Making move: GameID=${gameData.game_id}, Token=${gameData.player_token}, Row=${rowIndex}, Side=${side}`)
        sendMakeMoveWebSocket(gameData.game_id, gameData.player_token, rowIndex, side)
    }

    // Determine current player's piece for display
    const currentPlayerPieceForControls = gameData ? gameData.player_piece : '?'
    const isMyTurn = gameData && gameState.current_player_token === gameData.player_token
    const controlsDisabled = !isMyTurn || gameState.status !== 'active' || isLoading

    if (!socketConnected && !error) {
        return (
            <Container centerContent py={{ base: "20vh", md: "30vh" }}>
                <VStack spacing={4}>
                    <Spinner
                        thickness="4px"
                        speed="0.65s"
                        emptyColor="gray.200"
                        color="teal.500"
                        size="xl"
                    />
                    <Text fontSize="lg" color="gray.600">Connecting to server...</Text>
                </VStack>
            </Container>
        )
    }
    if (error && (!gameData || !socketConnected)) {
        return (
            <Container centerContent py={{ base: "20vh", md: "30vh" }}>
                <VStack spacing={4} p={6} borderWidth="1px" borderRadius="lg" shadow="md" bg="white">
                    <Heading color="red.500" size="lg">Connection Error</Heading>
                    <Text color="gray.700" textAlign="center">{error}</Text>
                    <Text mt={2} fontSize="sm" color="gray.500">
                        Please ensure the backend server is running and try refreshing the page.
                    </Text>
                    <Button colorScheme="teal" onClick={() => window.location.reload()} mt={4}>
                        Refresh Page
                    </Button>
                </VStack>
            </Container>
        )
    }

    if (!gameData || gameState.status === 'setup' || gameState.status === 'waiting') {
        return (
            <Container centerContent py={10}>
                <GameSetup
                    setIsLoading={setIsLoading}
                    setError={setError}
                />
                {error && <Text color="red.500" mt={4}>Error: {error}</Text>}
            </Container>
        )
    }


    return (
        <Container maxW="container.md" py={6}>
            <VStack spacing={6} align="stretch">
                <Heading as="h1" size="xl" textAlign="center" color="teal.600" mb={2}>
                    Side-Stacker
                </Heading>

                <GameInfo gameData={gameData} gameState={gameState} />

                <Board boardData={gameState.board} />

                {gameState.status === 'active' && (
                    <Controls
                        onMakeMove={handleMakeMove}
                        isDisabled={controlsDisabled}
                        currentPlayerPiece={currentPlayerPieceForControls}
                    />
                )}

                {isLoading &&
                    <Spinner
                        label="Processing..."
                        thickness="4px"
                        speed="0.65s"
                        emptyColor="gray.200"
                        color="blue.500"
                        size="xl"
                    />
                }
                {error && !isLoading &&
                    <Text color="red.500" mt={2} textAlign="center">
                        Error: {error}
                    </Text>
                }

                {(gameState.status !== 'active' &&
                    gameState.status !== 'setup' &&
                    gameState.status !== 'waiting') && (
                        <Button
                            onClick={resetGameState}
                            colorScheme="pink"
                            size="lg"
                            mt={4}
                            isFullWidth
                        >
                            Play Again (New Game)
                        </Button>
                    )}
            </VStack>
        </Container>
    )

}

export default GamePage