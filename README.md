      
# Side-Stacker Game

![Side-Stacker Gameplay](./assets/screenshot-pvp-inprogress.png)


## Table of Contents

- [Side-Stacker Game](#side-stacker-game)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Features](#features)
  - [Tech Stack](#tech-stack)
  - [Project Structure](#project-structure)
  - [Setup and Installation](#setup-and-installation)
    - [Prerequisites](#prerequisites)
    - [Running with Docker (Recommended)](#running-with-docker-recommended)
    - [Manual Setup (Alternative - More Complex)](#manual-setup-alternative---more-complex)
  - [How to Play](#how-to-play)
  - [Game Modes](#game-modes)
  - [Screenshots](#screenshots)
  - [Future Enhancements](#future-enhancements)
  - [Known Issues / Limitations](#known-issues--limitations)

## Introduction

Side-Stacker is a web-based, two-player strategy game similar to Connect Four, but with a twist: pieces are stacked from either side of the rows instead of being dropped from the top. The game is played on a 7x7 grid. Players (or AI opponents) take turns placing their pieces ('X' or 'O') into a chosen row from the left or right side. The piece stacks inwards from the chosen side into the first available empty cell in that row.

The game ends when:
- A player gets four of their pieces consecutively in a row (horizontally, vertically, or diagonally).
- The board is completely full, resulting in a draw.

This project implements real-time multiplayer gameplay using WebSockets, AI opponents with varying difficulty levels, and persists game state in a backend database.

## Features

- **Real-time Gameplay:** See opponent's moves instantly without page refresh using WebSockets.
- **Multiple Game Modes:**
    - **Player vs Player (PvP):** Play against another human player.
    - **Player vs AI (PvE):** Challenge an AI opponent.
        - Easy Difficulty
        - Medium Difficulty (Minimax-based)
        - Hard Difficulty (Enhanced Minimax)
    - **AI vs AI (AvA):** Spectate a game between two AI opponents.
- **Interactive UI:** Clean and user-friendly interface built with React and Chakra UI.
- **Persistent Game State:** Game progress is saved in a PostgreSQL database.
- **Responsive Design:** Basic responsiveness for enjoyable play on various screen sizes (primarily desktop-focused).
- **Dark Theme:** Easy-on-the-eyes dark theme for comfortable gameplay.

## Tech Stack

- **Frontend:**
    - React (with JavaScript)
    - Vite (Build tool & Dev Server)
    - Chakra UI (Component Library & Styling)
    - React State (State Management)
    - WebSockets (native browser API)
- **Backend:**
    - Python 3.9+
    - FastAPI (Web Framework)
    - Uvicorn (ASGI Server)
    - WebSockets (FastAPI native support)
    - SQLAlchemy (ORM for database interaction)
    - Alembic (Database Migrations)
    - Pydantic (Data Validation)
- **Database:**
    - PostgreSQL
- **Containerization:**
    - Docker
    - Docker Compose
- **AI:**
    - Rule-based (Easy)
    - Minimax with Alpha-Beta Pruning (Medium, Hard)
- **Code Formatting:**
    - Prettier (Frontend)
    - Black (Backend)
- **Version Control:**
    - Git & GitHub

## Project Structure

    

IGNORE_WHEN_COPYING_START
Use code with caution. Markdown
IGNORE_WHEN_COPYING_END

side-stacker-game/
├── assets/ # Screenshots and other static assets for README
├── backend/ # FastAPI backend application
│ ├── app/ # Core application logic
│ │ ├── api/ # API endpoints (HTTP and WebSocket)
│ │ ├── core/ # Configuration
│ │ ├── crud/ # Database CRUD operations
│ │ ├── db/ # Database models, session, migrations (Alembic)
│ │ ├── schemas/ # Pydantic schemas
│ │ └── services/ # Business logic (game_logic, AI bots)
│ ├── tests/ # Backend unit tests
│ ├── alembic.ini # Alembic configuration
│ ├── Dockerfile # Dockerfile for backend
│ ├── pyproject.toml # Project metadata, Black config
│ └── requirements.txt # Python dependencies
├── frontend/ # React frontend application
│ ├── public/ # Static assets for frontend
│ ├── src/ # Frontend source code
│ │ ├── assets/ # Frontend-specific assets (images, etc.)
│ │ ├── components/ # Reusable React components
│ │ ├── contexts/ # React Context for state (if used)
│ │ ├── hooks/ # Custom React hooks (if used)
│ │ ├── pages/ # Page-level components
│ │ ├── services/ # API/WebSocket service logic
│ │ └── styles/ # Global styles, theme overrides
│ ├── .env.development # Environment variables for frontend dev
│ ├── .prettierrc.js # Prettier configuration
│ ├── Dockerfile # Dockerfile for frontend
│ ├── index.html # Main HTML file
│ ├── package.json # NPM dependencies and scripts
│ └── vite.config.js # Vite configuration
├── .gitignore
├── DESIGN.MD # Project design document
├── docker-compose.yml # Docker Compose configuration
└── README.md # This file

      
## Setup and Installation

### Prerequisites

- Docker and Docker Compose installed on your system.
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Git (for cloning the repository)
- A modern web browser (Chrome, Firefox, Edge, Safari)

### Running with Docker (Recommended)

This is the simplest way to get the application running locally.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/<your-username>/side-stacker-game.git
    cd side-stacker-game
    ```

2.  **Create environment files (if they don't exist from the repo):**
    The backend requires a `.env` file. If it's not present, copy the example:
    ```bash
    cp backend/.env.example backend/.env
    ```
    The frontend can use `.env.development` for `VITE_WS_BASE_URL`. If not present:
    ```bash
    # Example: cp frontend/.env.development.example frontend/.env.development
    # Or create frontend/.env.development with:
    # VITE_WS_BASE_URL=ws://localhost:8000/api/v1/ws-game/ws 
    # (Adjust if your WebSocket path differs)
    ```
    *(Note: Ensure the `DATABASE_URL` in `backend/.env` points to `db:5432` as configured in `docker-compose.yml`)*

3.  **Build and run the Docker containers:**
    From the root of the project directory (`side-stacker-game/`), run:
    ```bash
    docker-compose up --build
    ```
    - The `--build` flag ensures images are built if they don't exist or if Dockerfiles have changed.
    - This will start the backend, frontend, and database services.
    - The first time you run this, it might take a few minutes to download base images and install dependencies.

4.  **Apply database migrations (if running for the first time or after model changes):**
    Open a new terminal window, navigate to the `backend` directory of the project, and run:
    ```bash
    cd backend
    docker-compose exec backend alembic upgrade head
    cd .. 
    ```
    *(This command needs to be run from the directory containing the `docker-compose.yml` if `backend` is not the context, or adjust the `docker-compose exec` command pathing. Simpler: from project root: `docker-compose exec backend alembic upgrade head`)*

5.  **Access the application:**
    - Frontend (Game): Open your browser to `http://localhost:5173`
    - Backend API Docs (Swagger UI): `http://localhost:8000/docs`

6.  **To stop the application:**
    Press `Ctrl+C` in the terminal where `docker-compose up` is running.
    To remove the containers (but keep volumes like DB data):
    ```bash
    docker-compose down
    ```
    To remove containers AND volumes (like database data - **use with caution**):
    ```bash
    docker-compose down -v
    ```

### Manual Setup (Alternative - More Complex)
*(Docker is the primary method, for setup and testing)*

1.  **Backend (Python/FastAPI):**
    - Create and activate a Python virtual environment.
    - Install dependencies: `pip install -r backend/requirements.txt`
    - Set up PostgreSQL database manually or ensure one is running.
    - Configure `backend/.env` with the correct `DATABASE_URL`.
    - Run database migrations: `cd backend; alembic upgrade head`
    - Run the FastAPI server: `cd backend; uvicorn app.main:app --reload`
2.  **Frontend (React/Vite):**
    - Install Node.js and npm/yarn.
    - Install dependencies: `cd frontend; npm install`
    - Create `frontend/.env.development` with `VITE_WS_BASE_URL` pointing to your backend.
    - Run the Vite dev server: `cd frontend; npm run dev`

## How to Play

1.  Navigate to the application in your browser (`http://localhost:5173`).
2.  You'll see the "Create New Game" setup screen.
3.  **Choose a Game Mode:**
    - **Player vs Player (PvP):**
        - Player 1 creates the game. The UI will show "Waiting for Player 2..." and a Game ID.
        - Player 2 (on another browser/tab, or a friend) will need the Game ID to join. *(Current UI doesn't have a "Join Game by ID" field - this is a manual step for now, e.g., by P2 connecting via WebSocket client and sending a JOIN_GAME message with the ID, or P1 sharing the full URL if we implement joining via URL params later).*
    - **Player vs AI (PvE):**
        - Select "Player vs AI" and choose the AI difficulty (Easy, Medium, or Hard).
        - Click "Create Game". The game starts immediately with you as Player X.
    - **AI vs AI (AvA):**
        - Select "AI vs AI" and choose the difficulties for AI 1 (X) and AI 2 (O).
        - Click "Create Game". The game starts immediately, and you spectate.
4.  **Making a Move:**
    - The game board is a 7x7 grid.
    - When it's your turn, control buttons will appear next to each row (one for the left side, one for the right).
    - Click the button corresponding to the side of the row where you want to place your piece.
    - Your piece ('X' or 'O') will stack into the first available empty cell from that side in the chosen row.
5.  **Winning/Drawing:**
    - The first player to get **four** of their pieces in a consecutive line (horizontally, vertically, or diagonally) wins the game.
    - If the board becomes completely full and no player has won, the game is a draw.
6.  **Game Over:**
    - A message will indicate the winner or if it's a draw.
    - A "Play Again (New Game)" button will appear to start a new setup.

## Game Modes

- **Player vs Player (PvP):** Two human players compete against each other in real-time.
- **Player vs AI (PvE):** A human player competes against an AI opponent.
    - **Easy AI:** Makes semi-random moves with basic win/block logic.
    - **Medium AI:** Uses the Minimax algorithm with a moderate search depth and heuristics.
    - **Hard AI:** Uses Minimax with a deeper search depth and a more sophisticated heuristic function for stronger play.
- **AI vs AI (AvA) (Spectator Mode):** Watch two AI opponents play against each other. You can choose the difficulty levels for both AIs.

## Screenshots



1.  **Game Setup Screen:**
    ![Game Setup Screen](./assets/game-setup.png)
    *(Description: Shows the initial screen where the user selects game mode (PvP, PvE, AvA) and AI difficulties.)*

2.  **Player vs Player (PvP) - In Progress:**
    ![PvP Game In Progress](./assets/pvp-active.png)
    *(Description: A mid-game view of a PvP match, showing the board, pieces, game info, and controls for the current player.)*

3.  **Player vs AI (PvE) - Medium AI - Player's Turn:**
    ![PvE Medium AI Turn](./assets/pve-medium-turn.png)
    *(Description: Player X's turn against the Medium AI. Shows the board state and controls enabled for the player.)*

4.  **AI vs AI (AvA) - Spectating:**
    ![AvA Spectate Mode](./assets/ava-spectate.png)
    *(Description: Spectating an AI vs AI game. Shows the board updating automatically as AIs make moves. No controls are visible for the spectator.)*

5.  **Game Over - Player Win:**
    ![Game Over - Player Wins](./assets/game-over-win.png)
    *(Description: The game over screen showing Player X (or O) as the winner, the final board state, and the "Play Again" button.)*

6.  **Game Over - Draw:**
    ![Game Over - Draw](./assets/game-over-draw.png)
    *(Description: The game over screen showing a draw, the full board, and the "Play Again" button.)*


## Future Enhancements

*(This section is optional but good to show foresight)*
- **UI for Joining PvP Games:** Allow Player 2 to enter a Game ID to join an existing PvP game.
- **Improved Visual Feedback:**
    - Highlight valid move spots on hover.
    - Animate piece placement.
    - Clearly highlight the winning line when the game ends.
- **User Authentication & Profiles:** Allow users to create accounts, track stats, and have persistent identities.
- **Matchmaking / Lobby:** A system to find opponents or list open games.
- **More Advanced AI:**
    - Transposition tables for Minimax to improve performance at deeper search depths.
    - More sophisticated MCTS implementation.
    - (Ambitious) Training a small neural network for board evaluation.
- **Spectator Mode for PvP/PvE:** Allow users to watch ongoing human or PvE games.
- **Game Replay:** Ability to review past games move by move.
- **Enhanced Styling & Theming:** More UI polish, light/dark mode toggle.

## Known Issues / Limitations

- **PvP Joining:** Currently, Player 2 joining a specific PvP game created by Player 1 requires manual coordination (e.g., P1 shares Game ID, P2 uses a WebSocket client tool to send JOIN_GAME). The UI does not yet support inputting a Game ID to join.
- **Performance of Hard AI:** With `search_depth=5` or higher, the Hard AI can take several seconds per move, which might impact user experience.
- **AvA Game Start:** The first move in an AvA game is triggered by an internal mechanism; there isn't a "start" button for the spectator once created.