// src/hooks/useGameStateManager.js
import { useState, useCallback, useEffect } from 'react';
import { useToast } from '@chakra-ui/react';
import { GAME_STATUS } from '../constants/gameConstants';
import { fetchUserStats as fetchUserStatsAPI } from '../services/httpService'; // Assuming httpService.js is created


const INITIAL_GAME_STATE = {
    board: Array(7).fill(Array(7).fill(null)),
    current_player_token: null,
    status: GAME_STATUS.SETUP, // 'setup', 'waiting', 'active', 'over'
    winner_token: null,
    players_map: {},
    last_move: null,
};

const INITIAL_USER_STATS = {
    games_played: 0,
    wins: 0,
    losses: 0,
    draws: 0,
    abandoned_by_user: 0,
    // These fields come from the backend schema, ensure they match
    // user_id: null,
    // username: '', // This will be stored in a separate 'username' state
    // updated_at: null,
};

const useGameStateManager = (clientId) => { // clientId is passed in (e.g. from useGameWebSocket)
    const [gameData, setGameData] = useState(null);
    const [gameState, setGameState] = useState(INITIAL_GAME_STATE);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const toast = useToast();

    // ### NEW LINE/BLOCK START ### Username and UserStats state ### NEW LINE/BLOCK END ###
    const [username, setUsername] = useState(''); // Local state for username
    const [userStats, setUserStats] = useState(INITIAL_USER_STATS); // Local state for stats
    const [statsLoading, setStatsLoading] = useState(false);
    const [statsError, setStatsError] = useState(null);

    // Effect to load username from localStorage on initial mount
    useEffect(() => {
        const storedUsername = localStorage.getItem('sideStackerUsername');
        const trimmedStoredUsername = storedUsername.trim();
        if (trimmedStoredUsername) {
            setUsername(trimmedStoredUsername);
        }
    }, []); // Empty dependency array: runs once on mount

    // Function to fetch and update user stats
    const fetchAndSetUserStats = useCallback(async (currentUsernameToFetch) => {
        const trimmedUsername = typeof currentUsernameToFetch === 'string' ? currentUsernameToFetch.trim() : '';
        if (!trimmedUsername) {
            setUserStats(INITIAL_USER_STATS); // Reset stats if username is invalid/cleared
            setStatsError(null);
            return;
        }
        setStatsLoading(true);
        setStatsError(null);
        console.log(`useGameStateManager: Attempting to fetch stats for ${trimmedUsername}`);
        try {
            const result = await fetchUserStatsAPI(trimmedUsername);
            if (result.success && result.data) {
                setUserStats({ // Ensure we map to the structure of INITIAL_USER_STATS
                    games_played: result.data.games_played ?? 0,
                    wins: result.data.wins ?? 0,
                    losses: result.data.losses ?? 0,
                    draws: result.data.draws ?? 0,
                    abandoned_by_user: result.data.abandoned_by_user ?? 0,
                    // Include other fields if needed by GameHistoryStats component
                    // user_id: result.data.user_id,
                    // username: result.data.username, // already have in 'username' state
                    // updated_at: result.data.updated_at,
                });
            } else {
                console.warn('useGameStateManager: Failed to fetch stats or no stats data found.', result.error);
                setUserStats(INITIAL_USER_STATS); // Reset to default if fetch fails
                // setStatsError(result.error || 'Could not load player statistics.');
                // Optionally toast only for unexpected errors
                if (result.error && !String(result.error).toLowerCase().includes('not found') && !String(result.error).toLowerCase().includes('invalid username')) {
                    toast({ title: "Stats Error", description: String(result.error), status: "warning", duration: 3000, isClosable: true });
                }
            }
        } catch (e) {
            console.error('useGameStateManager: Exception while fetching stats:', e);
            setUserStats(INITIAL_USER_STATS);
            setStatsError('An unexpected error occurred while fetching statistics.');
            toast({ title: "Stats Error", description: "Could not load statistics.", status: "error", duration: 3000, isClosable: true });
        } finally {
            setStatsLoading(false);
        }
    }, [toast]); // Added toast dependency

    // Effect to fetch stats when username changes (and is not empty)
    useEffect(() => {
        const trimmedUsername = typeof username === 'string' ? username.trim() : '';
        if (trimmedUsername) {
            fetchAndSetUserStats(username);
        } else {
            // If username is cleared or becomes invalid, reset stats
            setUserStats(INITIAL_USER_STATS);
            setStatsError(null); // Clear any previous stats errors
        }
    }, [username, fetchAndSetUserStats]); // Dependencies

    const resetGame = useCallback(() => {
        setGameData(null);
        setGameState(INITIAL_GAME_STATE);
        setError(null);
        setIsLoading(false);
        const currentTrimmedUsername = typeof username === 'string' ? username.trim() : '';
        if (currentTrimmedUsername) {
            fetchAndSetUserStats(currentTrimmedUsername); // Pass the current, known valid username
        }
    }, [username, fetchAndSetUserStats]);

    const handleGameCreatedOrJoined = useCallback((payload, messageType) => { // Added messageType for context
        console.log(`useGameStateManager: Game created/joined:`, payload);
        // This is useful if the backend canonicalizes the username (e.g., case)
        // or if the user is joining and didn't have a username set locally yet.
        const usernameFromServer = payload.username;
        if (typeof usernameFromServer === 'string') {
            const trimmedUsernameFromServer = usernameFromServer.trim();
            if (trimmedUsernameFromServer && trimmedUsernameFromServer !== username) {
                console.log(`useGameStateManager: Updating username from server: "${trimmedUsernameFromServer}"`);
                setUsername(trimmedUsernameFromServer);
                localStorage.setItem('sideStackerUsername', trimmedUsernameFromServer);
            } else if (!username && trimmedUsernameFromServer) {
                console.log(`useGameStateManager: Setting username from server (local was empty): "${trimmedUsernameFromServer}"`);
                setUsername(trimmedUsernameFromServer);
                localStorage.setItem('sideStackerUsername', trimmedUsernameFromServer);
            }
        }

        setGameData({
            game_id: payload.game_id,
            player_token: payload.player_token === "SPECTATOR" ? clientId : payload.player_token,
            player_piece: payload.player_piece,
            game_mode: payload.game_mode,
        });
        if (payload.message) {
            toast({
                title: payload.message,
                status: (payload.game_mode?.startsWith("PVP") && payload.player_piece === "X" && messageType === "GAME_CREATED") ? "info" : "success",
                duration: 3000,
                isClosable: true,
            });
        }
        setIsLoading(false);
        setError(null);
    }, [toast, clientId, username, setUsername]); // Ensure setUsername is a dep if used to update state

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
        if (payload.your_token && payload.your_piece && gameData?.player_token !== payload.your_token) {
            setGameData(prevData => ({
                ...prevData,
                game_id: payload.game_id || prevData?.game_id,
                player_token: payload.your_token,
                player_piece: payload.your_piece,
                game_mode: payload.game_mode || prevData?.game_mode
            }));
        }
        toast({
            title: `Game Started! It's ${payload.players[payload.current_player_token] || 'Unknown'}'s turn.`,
            status: "success",
            duration: 3000,
            isClosable: true,
        });
    }, [toast, gameData]);

    const handleGameUpdate = useCallback((payload) => {
        console.log("useGameStateManager: GAME_UPDATE received", payload);
        setGameState(prevState => ({
            ...prevState,
            board: payload.board,
            current_player_token: payload.current_player_token,
            last_move: payload.last_move,
            status: GAME_STATUS.ACTIVE,
        }));
    }, []);

    const handleGameOver = useCallback((payload) => {
        console.log("useGameStateManager: GAME_OVER received", payload);
        setGameState(prevState => ({
            ...prevState,
            board: payload.board,
            current_player_token: null,
            status: payload.status,
            winner_token: payload.winner_token,
            game_over_reason: payload.reason || null
        }));
        let titleText = "Game Over!";
        let descriptionText = null;
        let toastStatus = "info";

        if (payload.reason === "opponent_disconnected") {
            if (payload.winner_token === gameData?.player_token) {
                titleText = "You Win by Forfeit!";
                descriptionText = "Your opponent disconnected from the game.";
                toastStatus = "success";
            } else if (payload.winner_token) {
                const winnerPiece = gameState.players_map[payload.winner_token] || payload.winning_player_piece || '?';
                titleText = `Player ${winnerPiece} Wins by Forfeit!`;
                descriptionText = `The other player disconnected.`;
                toastStatus = "warning";
            } else {
                titleText = "Game Ended: Opponent Disconnected";
                toastStatus = "warning";
            }
        } else if (payload.status === GAME_STATUS.DRAW) { // Changed from winner_token === GAME_STATUS.DRAW
            titleText = "It's a Draw!";
            toastStatus = "warning";
        } else if (payload.winner_token) {
            const winnerPiece = gameState.players_map[payload.winner_token] || payload.winning_player_piece || '?';
            titleText = `Player ${winnerPiece} Wins!`;
            toastStatus = gameData?.player_token === payload.winner_token ? "success" : "error";
        }
        toast({
            title: titleText,
            description: descriptionText,
            status: toastStatus,
            duration: 4000,
            isClosable: true,
        });
        const currentTrimmedUsername = typeof username === 'string' ? username.trim() : '';
        if (currentTrimmedUsername) {
            fetchAndSetUserStats(currentTrimmedUsername); // Pass the current, known valid username
        }
    }, [toast, gameState.players_map, gameData?.player_token, username, fetchAndSetUserStats]);

    const handleWaitingForPlayer = useCallback((payload) => {
        console.log("useGameStateManager: WAITING_FOR_PLAYER received:", payload);
        toast.close("waiting-toast");
        toast({
            id: "waiting-toast",
            title: "Waiting for opponent...",
            description: `Share Game ID: ${payload.game_id}`,
            status: "info",
            duration: null,
            isClosable: true,
        });
        setGameState(prevState => ({ ...prevState, status: GAME_STATUS.WAITING }));
    }, [toast]);

    const handleExternalError = useCallback((errorMessage) => {
        console.error("useGameStateManager: External Error:", errorMessage);
        setError(errorMessage);
        // Optionally, display a toast for external errors if not handled elsewhere
        // toast({ title: "Connection Issue", description: String(errorMessage), status: "error", duration: 5000, isClosable: true });
    }, []); // Removed toast from deps if not used, or add if toast is used


    return {
        gameData,
        gameState,
        isLoading,
        error,
        username,           // Current username
        setUsername,        // Allow GameSetup or other components to set username if needed (e.g., from localStorage)
        userStats,          // Current user stats
        statsLoading,       // Loading state for stats fetching
        statsError,         // Error state for stats fetching
        fetchUserStats: fetchAndSetUserStats, // Expose the fetching function
        setIsLoading,
        setError,
        resetGame,
        handleGameCreatedOrJoined,
        handleGameStart,
        handleGameUpdate,
        handleGameOver,
        handleWaitingForPlayer,
        handleExternalError,
    };
};

export default useGameStateManager;