// src/hooks/useGameStateManager.js (New File)
import { useState, useCallback } from 'react';
import { useToast } from '@chakra-ui/react';
import { GAME_STATUS } from '../constants/gameConstants'

const INITIAL_GAME_STATE = {
    board: Array(7).fill(Array(7).fill(null)),
    current_player_token: null,
    status: GAME_STATUS.SETUP, // 'setup', 'waiting', 'active', 'over'
    winner_token: null,
    players_map: {},
    last_move: null,
};

const useGameStateManager = (clientId) => {
    const [gameData, setGameData] = useState(null);
    const [gameState, setGameState] = useState(INITIAL_GAME_STATE);
    const [isLoading, setIsLoading] = useState(false); // General loading for game actions
    const [error, setError] = useState(null); // General game error
    const toast = useToast();

    const resetGame = useCallback(() => {
        setGameData(null);
        setGameState(INITIAL_GAME_STATE);
        setError(null);
        setIsLoading(false);
    }, []);

    const handleGameCreatedOrJoined = useCallback((payload) => {
        console.log(`useGameStateManager: Game created/joined:`, payload);
        setGameData({
            game_id: payload.game_id,
            player_token: payload.player_token === "SPECTATOR" ? clientId : payload.player_token,
            player_piece: payload.player_piece,
            game_mode: payload.game_mode,
        });
        if (payload.message) {
            toast({
                title: payload.message,
                status: (payload.game_mode?.startsWith("PVP") && payload.player_piece === "X") ? "info" : "success",
                duration: 3000,
                isClosable: true,
            });
        }
        setIsLoading(false); // Specifically for game setup loading
        setError(null);
    }, [toast, clientId]);

    const handleGameStart = useCallback((payload) => {
        console.log("useGameStateManager: GAME_START received", payload);
        setGameState(prevState => ({
            ...prevState,
            board: payload.board,
            current_player_token: payload.current_player_token,
            players_map: payload.players,
            status: GAME_STATUS.ACTIVE,
            winner_token: null,
            last_move: null,
        }));
        // Update gameData if 'your_token' and 'your_piece' are in GAME_START and differ (e.g. on reconnect)
        if (payload.your_token && payload.your_piece && gameData?.player_token !== payload.your_token) {
            setGameData(prevData => ({
                ...prevData, // Keep existing game_id and game_mode if not in payload
                game_id: payload.game_id || prevData?.game_id,
                player_token: payload.your_token,
                player_piece: payload.your_piece,
                // game_mode might also come in GAME_START, if so, update it
                game_mode: payload.game_mode || prevData?.game_mode
            }));
        }
        toast({
            title: `Game Started! It's ${payload.players[payload.current_player_token] || 'Unknown'}'s turn.`,
            status: "success",
            duration: 3000,
            isClosable: true,
        });
    }, [toast, gameData, clientId]); // gameData added as dependency

    const handleGameUpdate = useCallback((payload) => {
        console.log("useGameStateManager: GAME_UPDATE received", payload);
        setGameState(prevState => ({
            ...prevState,
            board: payload.board,
            current_player_token: payload.current_player_token,
            last_move: payload.last_move,
            status: GAME_STATUS.ACTIVE, // Ensure status remains active
        }));
    }, []);

    const handleGameOver = useCallback((payload) => {
        console.log("useGameStateManager: GAME_OVER received", payload);
        setGameState(prevState => ({
            ...prevState,
            board: payload.board,
            current_player_token: null,
            status: payload.status, // e.g., "player_x_wins", "draw"
            winner_token: payload.winner_token,
            game_over_reason: payload.reason || null
        }));
        let titleText = "Game Over!";
        let descriptionText = null; // Optional description for toast
        let toastStatus = "info"; // Default toast status

        if (payload.reason === "opponent_disconnected") {
            if (payload.winner_token === gameData?.player_token) { // Check if I am the winner
                titleText = "You Win by Forfeit!";
                descriptionText = "Your opponent disconnected from the game.";
                toastStatus = "success";
            } else if (payload.winner_token) { // Opponent won because I disconnected (shouldn't happen if this client is still connected)
                // Or if it's a spectator view and one player disconnected
                const winnerPiece = gameState.players_map[payload.winner_token] || payload.winning_player_piece || '?';
                titleText = `Player ${winnerPiece} Wins by Forfeit!`;
                descriptionText = `The other player disconnected.`;
                toastStatus = "warning"; // Or info
            } else { // Should not happen in a 2-player game disconnect scenario if one wins by forfeit
                titleText = "Game Ended: Opponent Disconnected";
                toastStatus = "warning";
            }
        } else if (payload.winner_token === GAME_STATUS.DRAW) { // Assuming 'draw' constant
            titleText = "It's a Draw!";
            toastStatus = "warning";
        } else if (payload.winner_token) {
            const winnerPiece = gameState.players_map[payload.winner_token] || payload.winning_player_piece || '?';
            titleText = `Player ${winnerPiece} Wins!`;
            toastStatus = gameData?.player_token === payload.winner_token ? "success" : "error"; // Or 'info' if I lost
        }
        toast({
            title: titleText,
            description: descriptionText,
            status: toastStatus,
            duration: 4000,
            isClosable: true,
        });
    }, [toast, gameState.players_map, gameData?.player_token]);

    const handleWaitingForPlayer = useCallback((payload) => {
        console.log("useGameStateManager: WAITING_FOR_PLAYER received:", payload);
        toast.close("waiting-toast"); // Ensure previous waiting toasts are closed
        toast({
            id: "waiting-toast",
            title: "Waiting for opponent...",
            description: `Share Game ID: ${payload.game_id}`,
            status: "info",
            duration: null, // Keep open until explicitly closed or game starts
            isClosable: true,
        });
        setGameState(prevState => ({ ...prevState, status: GAME_STATUS.WAITING }));
    }, [toast]);

    const handleExternalError = useCallback((errorMessage) => { // For errors from socket or other sources
        console.error("useGameStateManager: External Error:", errorMessage);
        setError(errorMessage); // Set the main game error
        // toast for connection errors specifically handled by useGameWebSocket potentially
        // but can also show a general error toast here if desired.
        // setIsLoading(false); // Ensure loading is stopped on error
    }, [toast]);


    return {
        gameData,
        gameState,
        isLoading,
        error,
        setIsLoading, // Expose for GameSetup
        setError,     // Expose for GameSetup
        resetGame,
        // WebSocket event handlers to be passed to useGameWebSocket
        handleGameCreatedOrJoined,
        handleGameStart,
        handleGameUpdate,
        handleGameOver,
        handleWaitingForPlayer,
        handleExternalError, // Renamed from handleWebSocketError
    };
};

export default useGameStateManager;