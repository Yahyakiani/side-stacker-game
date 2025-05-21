// frontend/src/components/GameInfo.jsx
import React from 'react'
import { Box, Text, Heading, Tag, VStack, HStack } from '@chakra-ui/react'

const GameInfo = ({ gameData, gameState }) => {
    if (!gameData || !gameState) {
        return null // Or a loading/placeholder state
    }

    const { player_piece: myPiece, player_token: myToken } = gameData
    const { current_player_token, status, winner_token, players_map } = gameState

    const isMyTurn = myToken === current_player_token
    const currentPlayerPieceDisplay = players_map && current_player_token ? players_map[current_player_token] : '?'

    let statusMessage = "Game In Progress"
    let statusColorScheme = "blue"

    if (status === 'waiting' || status === 'waiting_for_player2') {
        statusMessage = "Waiting for opponent..."
        statusColorScheme = "orange"
    } else if (status.includes("wins")) {
        const winnerPieceDisplay = players_map && winner_token ? players_map[winner_token] : '?'
        statusMessage = `Player ${winnerPieceDisplay} Wins!`
        statusColorScheme = winner_token === myToken ? "green" : "red"
    } else if (status === "draw") {
        statusMessage = "It's a Draw!"
        statusColorScheme = "gray"
    }

    return (
        <Box p={4} borderWidth="1px" borderRadius="lg" shadow="sm" bg="white">
            <VStack spacing={3} align="stretch">
                <Heading size="md" textAlign="center">Game Status</Heading>

                <Tag size="lg" variant="subtle" colorScheme={statusColorScheme} justifyContent="center" py={2}>
                    {statusMessage}
                </Tag>

                {status === 'active' && current_player_token && (
                    <Text textAlign="center" fontSize="lg" fontWeight="bold" color={isMyTurn ? "green.600" : "orange.600"}>
                        Turn: Player {currentPlayerPieceDisplay}
                        {isMyTurn && " (Your Turn)"}
                    </Text>
                )}

                <HStack justifyContent="space-between" fontSize="sm" color="gray.600">
                    <Text>You are Player: <Text as="span" fontWeight="bold" color={myPiece === 'X' ? 'red.500' : 'blue.500'}>{myPiece}</Text></Text>
                    <Text>Game ID: <Text as="span" fontStyle="italic">{gameData.game_id.substring(0, 8)}...</Text></Text>
                </HStack>
            </VStack>
        </Box>
    )
}

export default GameInfo