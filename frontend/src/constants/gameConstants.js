// frontend/src/constants/gameConstants.js

// Board Dimensions & Layout
export const NUM_ROWS = 7;
export const NUM_COLS = 7; // Assuming a square board, useful for Board component
export const BOARD_CELL_SIZE_PX = 50; // Cell size in pixels
export const BOARD_GAP_PX = 2;       // Gap between cells in pixels

// Game Statuses (as used in GamePage and GameInfo)
export const GAME_STATUS = {
    SETUP: 'setup',
    WAITING: 'waiting', // Covers P1 waiting for P2, and P2 joining before game starts
    ACTIVE: 'active',
    PLAYER_X_WINS: 'player_x_wins', // Example specific win status
    PLAYER_O_WINS: 'player_o_wins', // Example specific win status
    DRAW: 'draw',
    INFO: 'info', // For informational messages
    ERROR: 'error', // For error messages
    // Add any other status strings your backend might send or frontend uses
    WAITING_FOR_PLAYER_2: 'waiting_for_player2', // Specific waiting status for P2
    GAME_OVER: 'game_over', // General game over status


};

export const USERNAME_PAYLOAD_KEY = "username";

// Player Pieces
export const PLAYER_PIECES = {
    X: 'X',
    O: 'O',
    NONE: null, // Or an empty string, depending on how you represent empty cells
};

// Game Modes (as used in GameSetup, GamePage, socketService)
export const GAME_MODES = {
    PVP: 'PVP', // Player vs Player
    PVE: 'PVE', // Player vs Environment (AI)
    AVA: 'AVA', // AI vs AI (Spectator)
};

// AI Difficulty Levels (as used in GameSetup, socketService)
export const AI_DIFFICULTY = {
    EASY: 'EASY',
    MEDIUM: 'MEDIUM',
    HARD: 'HARD',
};

// WebSocket Message Types (as used in socketService and potentially hooks)
// This list can be expanded based on all message types your application uses.
export const WS_MSG_TYPES = {
    // Client to Server
    CREATE_GAME: "CREATE_GAME",
    JOIN_GAME: "JOIN_GAME",
    MAKE_MOVE: "MAKE_MOVE",

    // Server to Client
    GAME_CREATED: "GAME_CREATED",
    GAME_JOINED: "GAME_JOINED",
    GAME_START: "GAME_START",
    GAME_UPDATE: "GAME_UPDATE",
    GAME_OVER: "GAME_OVER",
    WAITING_FOR_PLAYER: "WAITING_FOR_PLAYER",
    ERROR: "ERROR",
    // Add any other custom message types
};

// Control Sides (as used in Controls.jsx and potentially game logic if it expects these strings)
export const CONTROL_SIDES = {
    LEFT: 'L',
    RIGHT: 'R',
};

// UI & Styling Constants (Example)
export const UI_CONSTANTS = {
    CONTROLS_BUTTON_WIDTH_PX: "100px",
    // You could put theme color names here if they are frequently used in JS logic,
    // but generally, Chakra UI's theme object handles this.
};

// Add other constants as you identify them
// e.g., API endpoints (though VITE_env vars are good for base URLs), default timeouts, etc.