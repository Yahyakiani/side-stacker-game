      
# DESIGN DOCUMENT: Side-Stacker Game

**Version:** 0.3.2 (JavaScript Edition - Style Note)
**Last Updated:** [Current Date - e.g., 2023-10-27]

## 1. Introduction

This document outlines the design and development plan for the "Side-Stacker" game. It's a two-player game similar to Connect-Four, but pieces are stacked from the sides of a 7x7 grid. The project includes a web-based interface, real-time multiplayer, AI opponents, and backend persistence.

The game involves two players taking turns placing their pieces ('X' or 'O') into one of the 7 rows, from either the left or right side. Pieces stack inwards from the chosen side. The game ends when a player achieves four consecutive pieces in a row, column, or diagonal, or when the board is full (resulting in a draw).

This document will be updated iteratively to reflect the current state of the project, completed tasks, and next steps.

## 2. Goals

*   Implement a 2-player Side-Stacker game with a 7x7 grid.
*   Players can see the board and make moves on their frontend.
*   Opponent's moves are reflected in real-time without page refresh using WebSockets.
*   Display clear win/loss/draw messages (e.g., "Player 1 won", "Player 2 lost").
*   Implement an AI bot with at least Easy and Medium difficulty levels using **traditional game AI algorithms (e.g., rule-based, Minimax)**.
*   Support game modes:
    *   Player vs Player (PvP) (Required)
    *   Player vs AI (PvE) (Required)
    *   AI vs AI (AvA) (Optional Stretch Goal)
*   Store game state in a relational database (PostgreSQL) on the backend.
*   Follow best programming practices: succinct, runnable, correct, and extendable code, resisting overengineering.
*   Develop a clean, simple, and good-looking UI using React with **JavaScript**.
*   Maintain a consistent code style. For JavaScript, we can aim for a style similar to Prettier.io defaults with no semicolons, but overall consistency is the key. For Python, Black will be used.

## 3. Non-Goals (Initially, for core requirements)

*   User authentication system (e.g., logins, user accounts). Player identification will be via temporary tokens/session IDs.
*   Complex matchmaking or lobby system beyond simple game creation/joining.
*   Player profiles, statistics, or leaderboards.
*   Advanced chat functionality beyond basic game events or status messages.
*   Mobile-specific responsive design (focus on desktop web first, though basic responsiveness via UI library is a plus).
*   AI implementation using external LLM APIs (e.g., Gemini) for **required Easy and Medium difficulties**.

## 4. Proposed Tech Stack

*   **Backend:** Python 3.9+ (or latest stable), FastAPI
*   **Frontend:** React (v18+) with **JavaScript** (ES6+)
*   **UI Library/Styling:** Chakra UI (recommended for its component quality, theming, and ease of use for a clean aesthetic).
*   **Code Formatting (Frontend):** Prettier (configured for no semicolons, or as per chosen consistent style).
*   **Code Formatting (Backend):** Black (Python standard).
*   **Real-time Communication:** WebSockets (via FastAPI's WebSocket support).
*   **Database:** PostgreSQL (latest stable, e.g., v15 or v16) run as a Docker service.
*   **ORM/DB Interaction:** SQLAlchemy (latest stable, e.g., v2.x) with Alembic for migrations.
*   **Containerization:** Docker, Docker Compose (latest stable versions).
*   **Code Management:** Git, GitHub.
*   **Development Environment:** Vite for React project setup and dev server.
*   **Testing:** Pytest for backend unit tests, React Testing Library / Jest for frontend tests (optional but recommended).

## 5. High-Level Architecture

    

IGNORE_WHEN_COPYING_START
Use code with caution. Markdown
IGNORE_WHEN_COPYING_END

+------------------------+ HTTP/S +-----------------+ WebSocket +------------------------+
| React Client |<--------------->| FastAPI Backend|<----------------->| React Client |
| (JavaScript,ChakraUI) | | (Python) | | (JavaScript,ChakraUI) |
| (Vite Dev Server) | | (Uvicorn) | | (Browser) |
+------------------------+ +--------+--------+ +------------------------+
^ |
| API Calls (e.g. initial load) | (SQLAlchemy ORM)
| WebSocket Messages |
| User Actions v
| Game State Updates +-----------------+
| | PostgreSQL |
| | (Dockerized) |
+---------------------------------------+-----------------+

      
*   **Client (React with JavaScript & Chakra UI):** Single Page Application (SPA) responsible for rendering the game UI. It will connect to the backend via WebSockets for real-time game interactions and potentially HTTP for initial setup or non-real-time data. State management within React will handle the board, player info, and game status. Code style will be kept consistent, aiming for Prettier defaults (e.g., no semicolons).
*   **Backend (FastAPI):** Python application server.
    *   Manages core game logic and state transitions.
    *   Handles WebSocket connections, managing game "rooms" or sessions.
    *   Orchestrates AI turns for PvE and AvA modes.
    *   Interacts with the PostgreSQL database via SQLAlchemy for persistence.
    *   Serves API endpoints for game management if needed (though most actions will be WebSocket-driven). Python code styled with Black.
*   **Database (PostgreSQL):** Persists game state, allowing games to be potentially listed or (in future) resumed, though the primary focus is on active game persistence.
*   **AI Bot:** Python modules integrated into the FastAPI application, callable by the game orchestration logic.

## 6. Component Breakdown

### 6.1. Backend (FastAPI)

*   **Project Structure (Illustrative):**
    ```
    backend/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py             # FastAPI app initialization, routers
    │   ├── core/
    │   │   └── config.py       # Settings, environment variables
    │   ├── db/
    │   │   ├── __init__.py
    │   │   ├── base_class.py   # Base for SQLAlchemy models
    │   │   ├── models.py       # SQLAlchemy models (e.g., Game)
    │   │   ├── session.py      # Database session management
    │   │   └── migrations/     # Alembic migration scripts
    │   ├── schemas/
    │   │   └── game.py         # Pydantic schemas for request/response validation
    │   ├── crud/
    │   │   └── crud_game.py    # CRUD operations for Game model
    │   ├── services/
    │   │   ├── game_logic.py   # Core game rules, board manipulation, win checks
    │   │   └── ai/
    │   │       ├── __init__.py
    │   │       ├── base_bot.py # Abstract base class for AI bots
    │   │       ├── easy_bot.py
    │   │       ├── medium_bot.py
    │   │       └── (hard_bot.py)
    │   └── api/
    │       └── v1/
    │           ├── __init__.py
    │           ├── endpoints/
    │           │   └── game_ws.py # WebSocket endpoint for game interactions
    │           └── deps.py        # Dependencies for endpoints
    ├── tests/                    # Pytest unit tests
    ├── alembic.ini
    ├── pyproject.toml            # For Black configuration, project metadata
    ├── Dockerfile
    └── requirements.txt
    ```
*   **Game Logic Module (`app/services/game_logic.py`):**
    *   Board representation: `List[List[Optional[str]]]` (e.g., `[['X', None, 'O'], ...]`). `str` could be 'X', 'O'.
    *   Constants for players (e.g., `PLAYER_X = "X"`, `PLAYER_O = "O"`), board dimensions (`ROWS = 7`, `COLS = 7`).
    *   Functions:
        *   `create_board()`: Returns a new empty 7x7 board.
        *   `is_valid_move(board, row: int, side: str) -> bool`: Checks if a piece can be placed in the given row from the given side ('L' or 'R').
        *   `apply_move(board, row: int, side: str, player: str) -> Tuple[int, int]`: Places the player's piece on the board from the specified side and returns the (row, col) of the placed piece.
        *   `check_win(board, player: str, last_move_coords: Tuple[int, int]) -> bool`: Checks for 4-in-a-row for `player` involving `last_move_coords`.
        *   `check_draw(board) -> bool`: Checks if the board is full.
*   **WebSocket Handler (`app/api/v1/endpoints/game_ws.py`):**
    *   Manages active WebSocket connections and game rooms (e.g., using a dictionary mapping `game_id` to a list of connections or a dedicated `ConnectionManager` class).
    *   Handles incoming messages based on `type` field (see Protocol section).
    *   Orchestrates game flow: creating games, adding players, processing moves, triggering AI, broadcasting updates.
*   **Database Models (`app/db/models.py` using SQLAlchemy):**
    *   `Game(Base)`:
        *   `id: Mapped[uuid.UUID]` (primary key, default `uuid.uuid4`)
        *   `player1_token: Mapped[str]` (unique identifier for player 1, e.g., a session UUID)
        *   `player2_token: Mapped[Optional[str]]` (for player 2, nullable for PvE or waiting PvP)
        *   `current_player_token: Mapped[Optional[str]]`
        *   `board_state: Mapped[dict]` (JSONB type, storing the `List[List[Optional[str]]]` board)
        *   `status: Mapped[str]` (e.g., 'WAITING_FOR_PLAYER2', 'ACTIVE', 'PLAYER1_WON', 'PLAYER2_WON', 'DRAW', 'AVA_ACTIVE')
        *   `game_mode: Mapped[str]` (e.g., 'PVP', 'PVE_EASY', 'PVE_MEDIUM', 'AVA_EASY_MEDIUM')
        *   `winner_token: Mapped[Optional[str]]`
        *   `created_at: Mapped[datetime]` (default `func.now()`)
        *   `updated_at: Mapped[datetime]` (default `func.now()`, onupdate `func.now()`)
*   **AI Module (`app/services/ai/`):**
    *   `BaseBot(ABC)`: Abstract base class with `get_move(board: List[List[Optional[str]]], player_piece: str) -> Tuple[int, str]` (row, side).
    *   `EasyAIBot(BaseBot)`: Implements easy logic.
    *   `MediumAIBot(BaseBot)`: Implements Minimax.
    *   (Optional) `HardAIBot(BaseBot)`: Advanced classical AI.
    *   (Optional Exploration) `LLMAIBot(BaseBot)`: For Gemini API interaction.

### 6.2. Frontend (React with JavaScript)

*   **Project Structure (Illustrative, using Vite):**
    ```
    frontend/
    ├── public/
    ├── src/
    │   ├── App.jsx  (or .js)
    │   ├── main.jsx (or .js)
    │   ├── assets/
    │   ├── components/
    │   │   ├── board/
    │   │   │   ├── Board.jsx
    │   │   │   └── Cell.jsx
    │   │   ├── ui/                # Generic UI elements if needed
    │   │   │   └── LoadingSpinner.jsx
    │   │   ├── GameInfo.jsx
    │   │   ├── Controls.jsx
    │   │   └── GameSetup.jsx
    │   ├── contexts/              # React Context for state management
    │   │   └── GameContext.js
    │   ├── hooks/                 # Custom hooks
    │   │   └── useWebSocket.js
    │   ├── services/
    │   │   └── socketService.js   # WebSocket communication logic
    │   ├── styles/
    │   │   └── theme.js           # Chakra UI custom theme
    │   └── pages/
    │       └── GamePage.jsx
    ├── .prettierrc.js             # Prettier configuration
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── Dockerfile (for building/serving static assets or running dev server)
    ```
*   **Core Components (using `.jsx` or `.js` extension, Chakra UI):**
    *   `App.jsx`: Main router (e.g., react-router-dom) for different pages (Home/Setup, Game). Chakra `ChakraProvider` wraps the app.
    *   `GamePage.jsx`: Orchestrates the game view, manages game state via Context or Zustand, handles WebSocket events.
    *   `Board.jsx`: Renders the 7x7 grid using Chakra `Grid` and `GridItem`. `Cell.jsx` instances populate the grid.
    *   `Cell.jsx`: A Chakra `Box` styled to represent a cell, displaying 'X', 'O', or an indicator for an empty, playable spot.
    *   `Controls.jsx`: For each row, provides Chakra `Button`s or clickable areas on the left and right sides to place a piece. Disables controls when not player's turn.
    *   `GameInfo.jsx`: Displays current turn (e.g., "Your Turn (X)"), game status/winner ("Player O Wins!", "Draw!"), error messages using Chakra `Text`, `Heading`, `Alert`.
    *   `GameSetup.jsx`: Forms using Chakra `RadioGroup`, `Select`, `Button` to choose game mode (PvP, PvE, AvA) and AI difficulty.
*   **State Management (`src/contexts/GameContext.js` or Zustand store):**
    *   `gameId: string | null`
    *   `playerId: string | null` (the client's unique token)
    *   `playerPiece: 'X' | 'O' | null`
    *   `board: (string | null)[][]`
    *   `currentPlayerToken: string | null`
    *   `gameStatus: 'setup' | 'waiting' | 'active' | 'over'`
    *   `winner: string | null | 'draw'`
    *   `webSocket: WebSocket | null`
    *   PropTypes can be used for basic type checking if desired.
*   **WebSocket Client Service (`src/services/socketService.js`):**
    *   Functions to `connect(gameId, playerId)`, `disconnect()`.
    *   Functions to send structured messages: `sendCreateGameMessage(mode, difficulty?)`, `sendJoinGameMessage(gameId, playerId)`, `sendMakeMoveMessage(row, side)`.
    *   Parses incoming messages and dispatches actions or updates context.
*   **Code Style:**
    *   Use Prettier for automated code formatting.
    *   Configure Prettier for no semicolons (e.g., in `.prettierrc.js`: `{ "semi": false }`).
    *   Other Prettier defaults (e.g., `singleQuote: true`, `trailingComma: 'es5'`) are generally good.
    *   The primary goal is consistency. Add a script to `package.json` like `"format": "prettier --write \"src/**/*.{js,jsx}\""`.

### 6.3. Database (PostgreSQL)

*   **Containerized Service:** Managed via `docker-compose.yml`.
    *   Persistent volume for data storage (`./postgres-data:/var/lib/postgresql/data`).
    *   Environment variables for `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.
*   **Schema:** Defined by SQLAlchemy models (`app/db/models.py`) and managed by Alembic migrations.
*   **Access:** The FastAPI backend will be the sole direct accessor of the database.

## 7. AI Bot Design Details

*   **Easy (`EasyAIBot`):**
    1.  Identify all valid moves.
    2.  If any valid move results in an immediate win for the AI, play it.
    3.  Else, if any valid move for the opponent would result in their immediate win, block that move if possible.
    4.  Else, pick a random valid move.
*   **Medium (`MediumAIBot`):**
    1.  Implement the Minimax algorithm.
    2.  Search depth: Start with 2-3 plies (e.g., AI move, Opponent response, AI move). This can be tuned.
    3.  Heuristic evaluation function for non-terminal board states:
        *   Assign large positive/negative scores for winning/losing states (e.g., +10000 for AI win, -10000 for opponent win).
        *   Count opportunities:
            *   `+100` for each 3-in-a-row for AI (with an open space to complete it).
            *   `+10` for each 2-in-a-row for AI (with open spaces to complete it).
            *   `-100` for each 3-in-a-row for opponent (with an open space).
            *   `-10` for each 2-in-a-row for opponent (with open spaces).
        *   Consider piece placement (e.g., central rows might offer more connection paths).
*   **Hard (Stretch Goal - Classical Approach - `HardAIBot`):**
    1.  Minimax with Alpha-Beta Pruning.
    2.  Increased search depth (e.g., 4-6 plies or more, depending on performance).
    3.  More sophisticated heuristic function: consider threats, multi-line traps, board control.
    4.  (Alternative) Monte Carlo Tree Search (MCTS): Good for games where heuristic evaluation is complex. Might be overkill but a valid advanced approach.

*   **Optional Advanced AI Exploration (e.g., for Hard AI or AI vs AI mode, as a stretch goal AFTER core requirements are met):**
    *   **Using an LLM (e.g., Gemini API via `LLMAIBot`):**
        *   **Prompting:** Send current board state, game rules, whose turn, and desired piece. Use Chain of Thought for better reasoning if supported.
        *   **Example Prompt Fragment:** "You are playing Side-Stacker. The board is 7x7. Pieces stack from the sides. Current board: [[...]]. It's your turn, you are 'O'. Which row (0-6) and side ('L' or 'R') should you play to maximize your chance of winning? Provide your answer as JSON: {\"row\": R, \"side\": \"S\"}."
        *   **Considerations:** Latency, cost, API rate limits, reliability of response format, complexity of prompt engineering. Primarily for demonstration/exploration.

## 8. WebSocket Communication Protocol (JSON Messages)

*   **Client to Server (C2S):**
    *   `{ "type": "CREATE_GAME", "payload": { "player_temp_id": "client_generated_uuid", "mode": "PVP" | "PVE" | "AVA", "difficulty": "EASY" | "MEDIUM" | "HARD" | null, "ai2_difficulty": "EASY" | "MEDIUM" | "HARD" | null } }`
    *   `{ "type": "JOIN_GAME", "payload": { "game_id": "server_game_uuid", "player_temp_id": "client_generated_uuid" } }`
    *   `{ "type": "MAKE_MOVE", "payload": { "game_id": "uuid", "player_token": "server_player_token", "row": number, "side": "L" | "R" } }`
    *   `{ "type": "REQUEST_RECONNECT", "payload": { "game_id": "uuid", "player_token": "server_player_token" } }` (Optional for handling disconnections)
*   **Server to Client(s) (S2C):**
    *   `{ "type": "GAME_CREATED", "payload": { "game_id": "uuid", "player_token": "p1_token", "player_piece": "X" } }` (To game creator)
    *   `{ "type": "WAITING_FOR_PLAYER", "payload": { "game_id": "uuid", "invite_code_or_link": "optional_link_for_pvp" } }`
    *   `{ "type": "PLAYER_JOINED", "payload": { "game_id": "uuid", "player_token": "p2_token", "player_piece": "O" } }` (To existing player when P2 joins)
    *   `{ "type": "GAME_START", "payload": { "game_id": "uuid", "board": (string|null)[][], "current_player_token": "pX_token", "players": { "p1_token": "X", "p2_token": "O" }, "your_piece": "X" | "O", "your_token": "server_player_token" } }` (To all players in the game)
    *   `{ "type": "GAME_UPDATE", "payload": { "game_id": "uuid", "board": (string|null)[][], "current_player_token": "player_token", "last_move": { "player_token": "str", "row": number, "col": number, "piece": "X"|"O" } | null } }`
    *   `{ "type": "GAME_OVER", "payload": { "game_id": "uuid", "board": (string|null)[][], "status": "WIN" | "DRAW", "winner_token": "player_token" | null, "winning_player_piece": "X" | "O" | null } }`
    *   `{ "type": "ERROR", "payload": { "message": "Error description", "details": {} } }`
    *   `{ "type": "RECONNECT_SUCCESS", "payload": { /* similar to GAME_START but with current state */ } }` (Optional)

## 9. Development Phases & Roadmap

This is a living section and will be updated as we progress.
**(Current Status: Design Phase Complete - Ready for Phase 0)**

### Phase 0: Project Setup
*   **Task:** Initialize GitHub repository (`side-stacker-game`).
*   **Task:** Add this `DESIGN.MD` (v0.3.2) to the repository root.
*   **Task:** Create root `docker-compose.yml` defining services: `backend`, `frontend`, `db`.
*   **Task:** Setup `backend/` directory:
    *   `Dockerfile` for Python/FastAPI.
    *   `requirements.txt` (FastAPI, Uvicorn, SQLAlchemy, psycopg2-binary, Alembic, Black).
    *   `pyproject.toml` for Black configuration and project metadata.
    *   Basic FastAPI app structure (`app/main.py`, `app/core/config.py`).
    *   Health check endpoint in FastAPI (`/api/v1/health`).
*   **Task:** Setup `frontend/` directory:
    *   Initialize React + **JavaScript** project using Vite (`npm create vite@latest frontend -- --template react`).
    *   Install Prettier (`npm install --save-dev prettier eslint-config-prettier`).
    *   Create `.prettierrc.js` (e.g., `{ "semi": false, "singleQuote": true, "trailingComma": "es5" }`).
    *   Add Prettier script to `package.json` (e.g., `"format": "prettier --write \"src/**/*.{js,jsx}\""`).
    *   `Dockerfile` for Vite dev server (or for building static assets later).
*   **Task:** Configure PostgreSQL service in `docker-compose.yml` with a persistent volume.
*   **Task:** Ensure all services can be started with `docker-compose up --build`.
*   **DONE:**
    *   [x] Initialize GitHub repository (`side-stacker-game`).
    *   [x] Add this `DESIGN.MD` (v0.3.2) to the repository root. (Also added README.md, .gitignore)
    *   [x] Create root `docker-compose.yml` defining services: `backend`, `frontend`, `db`.
    *   [x] Configure PostgreSQL service in `docker-compose.yml` with a persistent volume. (Done as part of docker-compose.yml creation)
    *   [x] Setup `backend/` directory:
        *   [x] `Dockerfile` for Python/FastAPI.
        *   [x] `requirements.txt`.
        *   [x] `pyproject.toml`.
        *   [x] Basic FastAPI app structure (`app/main.py`, `app/core/config.py`, `.env.example`, `.env`).
        *   [x] Health check endpoint in FastAPI (`/api/v1/health`).
    *   [x] Setup `frontend/` directory:
        *   [x] Initialize React + **JavaScript** project using Vite.
        *   [x] Install Prettier.
        *   [x] Create `.prettierrc.js`.
        *   [x] Add Prettier script to `package.json`.
        *   [x] `Dockerfile` for Vite dev server.
    *   [x] Ensure all services can be started with `docker-compose up --build` and verified.

### Phase 1: Core Game Logic & Basic Backend (No DB/WebSockets yet)
*   **Task:** Implement Python game logic in `backend/app/services/game_logic.py` (board creation, move validation, apply move, win/draw checks).
*   **Task:** Write unit tests for `game_logic.py` using `pytest` in `backend/tests/`.
*   **Task:** Create temporary HTTP FastAPI endpoints to test game logic interactively (e.g., create game, make move, get board - all in-memory for now).
*   **DONE:**
    *   [x] Implemented Python game logic in `backend/app/services/game_logic.py`.
    *   [x] Wrote unit tests for `game_logic.py` using `pytest`.
    *   [x] Created and verified temporary HTTP FastAPI endpoints (`/api/v1/temp-game`) for interactive testing of game logic (in-memory).


### Phase 2: Database Integration
*   **Task:** Define SQLAlchemy models for `Game` in `backend/app/db/models.py`.
*   **Task:** Setup Alembic for database migrations (`backend/app/db/migrations/`).
*   **Task:** Create initial migration for the `games` table.
*   **Task:** Implement database session management in FastAPI (`backend/app/db/session.py`).
*   **Task:** Implement CRUD operations for games (`backend/app/crud/crud_game.py`).
*   **Task:** Modify backend game management (the temporary HTTP endpoints for now, later WebSockets) to save and load game state from PostgreSQL instead of in-memory.
*   **DONE:**
    *   [x] Defined SQLAlchemy `Game` model.
    *   [x] Setup Alembic and configured `env.py`.
    *   [x] Created and applied initial migration for `games` table.
    *   [x] Implemented `get_db` session management.
    *   [x] Implemented `crud_game.py` with `get_game`, `create_game_db`, `update_game_state`.
    *   [x] Modified temporary HTTP endpoints (`temp_game_http.py`) to use the database for all game operations (create, get state, make move). Verified database persistence of moves.
*   **NEXT:** Phase 3: Basic Frontend & WebSocket Foundation

### Phase 3: Basic Frontend & WebSocket Foundation
*   **Task:** Install and setup Chakra UI in the `frontend/` (JavaScript React) project. Define a basic theme.
*   **Task:** Implement WebSocket connection manager in FastAPI (`backend/app/api/v1/endpoints/game_ws.py` or a helper class).
*   **Task:** Define initial WebSocket message handlers in FastAPI for `CREATE_GAME` (PvP mode initially). Game creation should now use the DB.
*   **Task:** Implement React components: `GameSetup.jsx` (mode selection), basic `Board.jsx` (static display for now), `GameInfo.jsx`.
*   **Task:** Implement client-side WebSocket logic (`frontend/src/services/socketService.js`) to send `CREATE_GAME` and receive `GAME_CREATED`, `WAITING_FOR_PLAYER`.
*   **Task:** Connect `GameSetup.jsx` to create a game via WebSocket. Display `game_id` and player token received. Ensure frontend code is formatted with Prettier.
*   **DONE:** [ ]
*   **NEXT:** Phase 4

### Phase 4: Full PvP Gameplay via WebSockets
*   **Task:** Implement full WebSocket messaging lifecycle in FastAPI for PvP: handling `JOIN_GAME`, `MAKE_MOVE`. Process moves using `game_logic.py`, update DB, and broadcast `GAME_START`, `GAME_UPDATE`, `GAME_OVER`, `ERROR` messages.
*   **Task:** Backend logic for turn management, player identification (X/O assignment).
*   **Task:** Frontend (`GamePage.jsx`, `Board.jsx`, `Controls.jsx`):
    *   Allow joining an existing game (if supporting direct join by ID, or automatic pairing).
    *   Full board interactivity for making moves; send `MAKE_MOVE` via WebSocket.
    *   Dynamically update `Board.jsx` and `GameInfo.jsx` based on `GAME_UPDATE`, `GAME_START` from server.
    *   Display win/loss/draw messages based on `GAME_OVER`.
    *   Clearly indicate whose turn it is and what piece each player is.
*   **DONE:** [ ]
*   **NEXT:** Phase 5

### Phase 5: Player vs AI (Easy Bot)
*   **Task:** Implement `EasyAIBot` logic in `backend/app/services/ai/easy_bot.py`.
*   **Task:** Integrate Easy AI into backend WebSocket flow:
    *   When a PvE (Easy) game is created, the backend notes this.
    *   After player's move, if it's AI's turn, backend invokes `EasyAIBot.get_move()`.
    *   Backend validates and applies AI's move, updates DB, broadcasts `GAME_UPDATE`.
*   **Task:** Update `frontend/src/components/GameSetup.jsx` to allow selection of "Player vs AI (Easy)" mode.
*   **DONE:** [ ]
*   **NEXT:** Phase 6

### Phase 6: Player vs AI (Medium Bot)
*   **Task:** Implement `MediumAIBot` logic (Minimax) in `backend/app/services/ai/medium_bot.py`.
*   **Task:** Integrate Medium AI into backend WebSocket flow similar to Easy AI.
*   **Task:** Update `frontend/src/components/GameSetup.jsx` to allow selection of "Player vs AI (Medium)" mode.
*   **DONE:** [ ]
*   **NEXT:** Phase 7

### Phase 7: Polish & Optional Features
*   **Task:** Thoroughly test all required game modes (PvP, PvE Easy, PvE Medium) and win/loss/draw conditions.
*   **Task:** Refine UI/UX: clear visual cues for playable moves, last move indication, smooth transitions, error handling.
*   **Task:** Code cleanup, add comments, ensure `README.md` is comprehensive for setup and running.
*   **Task:** (Optional Stretch Goal) Implement AI vs AI mode:
    *   Backend orchestration for AvA games via WebSockets.
    *   Frontend UI to select AI opponents and spectate/trigger game.
*   **Task:** (Optional Stretch Goal) Implement a "Hard" AI using classical methods (`HardAIBot`).
*   **Task:** (Optional Exploration) If time/interest, experiment with LLM-based AI for AvA or Hard mode.
*   **Task:** Add basic frontend unit/component tests (React Testing Library / Jest).
*   **DONE:** [ ]
*   **NEXT:** Project Completion

## 10. Future Considerations (Beyond Initial Scope)

*   User accounts and authentication (e.g., FastAPI Users, JWT).
*   Persistent player statistics and leaderboards.
*   More sophisticated matchmaking/lobby (e.g., list of open games, random pairing).
*   Spectator mode for live games.
*   Game replay functionality (would likely require saving all moves to the DB).
*   Improved responsive design for various screen sizes.
*   Animations for piece placement and game events.