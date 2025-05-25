// frontend/src/components/GameInfo.jsx
import { Box, Text, Heading, Tag, VStack, HStack, Button, useClipboard, useToast, Icon } from '@chakra-ui/react'
import { GAME_STATUS } from '../constants/gameConstants'
import { FaCopy } from 'react-icons/fa'

const GameInfo = ({ gameData, gameState }) => {
    if (!gameData || !gameState) {
        return null // Or a loading/placeholder state
    }

    const { player_piece: myPiece, player_token: myToken, game_mode: gameMode } = gameData
    const { current_player_token, status, winner_token, players_map, game_over_reason } = gameState

    const isSpectator = gameMode && gameMode.startsWith('AVA')

    const isMyTurn = myToken === current_player_token
    const currentPlayerPieceDisplay = players_map && current_player_token ? players_map[current_player_token] : '?'

    let statusMessage = "Game In Progress"
    let statusColorScheme = "blue"

    const { onCopy, hasCopied } = useClipboard(gameData.game_id)
    const toast = useToast()



    if (status === GAME_STATUS.WAITING || status === GAME_STATUS.WAITING_FOR_PLAYER_2) {
        statusMessage = "Waiting for opponent..."
        statusColorScheme = "orange"
    } else if (game_over_reason === "opponent_disconnected") {
        // This is the new specific handling
        if (winner_token && players_map[winner_token]) {
            const winnerPieceDisplay = players_map[winner_token];
            statusMessage = `Player ${winnerPieceDisplay} Wins! (Opponent Left)`;
            statusColorScheme = (gameData?.player_token === winner_token) ? "green" : "red";
        } else {
            statusMessage = "Opponent Disconnected"; // Fallback
            statusColorScheme = "yellow";
        }
    } else if (status.includes("wins")) {
        const winnerPieceDisplay = players_map && winner_token ? players_map[winner_token] : '?'
        statusMessage = `Player ${winnerPieceDisplay} Wins!`
        statusColorScheme = winner_token === myToken ? "green" : "red"
    } else if (status === GAME_STATUS.DRAW) {
        statusMessage = "It's a Draw!"
        statusColorScheme = "gray"
    }

    const handleCopyGameId = () => {
        onCopy()
        toast({
            title: "Game ID Copied!",
            status: "success",
            duration: 2000,
            isClosable: true,
        })
    }

    return (
        <Box p={4} borderWidth="1px" borderRadius="lg" shadow="sm" bg="gray.700" color="whiteAlpha.900"> 
            <VStack spacing={3} align="stretch">
                <Heading size="md" textAlign="center" color="teal.300">Game Status</Heading> 

                <Tag size="lg" variant="subtle" colorScheme={statusColorScheme} justifyContent="center" py={2} bg={`${statusColorScheme}.600`} color="white"> {/* Custom Tag bg for dark mode */}
                    {statusMessage}
                </Tag>

                {/* Turn Indicator */}
                {status === GAME_STATUS.ACTIVE && current_player_token && (
                    <Text textAlign="center" fontSize="lg" fontWeight="bold" color={isMyTurn ? "green.300" : (isSpectator ? "white.300" : "orange.300")}>
                        Turn: Player {currentPlayerPieceDisplay}
                        {isMyTurn && " (Your Turn)"}
                        {isSpectator && " (AI Playing)"}
                    </Text>
                )}

                {/* Player Info / Spectator Info & Game ID */}
                <HStack justifyContent="space-between" fontSize="sm" color="gray.300">
                    <Box>
                        {isSpectator ? (
                            <Text fontWeight="bold" color="purple.300">Mode: Spectating AI vs AI</Text>
                        ) : (
                            <Text>You are Player: <Text as="span" fontWeight="bold" color={myPiece === 'X' ? 'orange.300' : 'white.300'}>{myPiece}</Text></Text>
                        )}
                    </Box>
                    <HStack>
                        <Text>Game ID: <Text as="span" fontStyle="italic" userSelect="all">{gameData.game_id.substring(0, 13)}...</Text></Text>
                        <Button
                            size="xs"
                            onClick={handleCopyGameId}
                            variant="ghost"
                            colorScheme="white"
                            aria-label="Copy Game ID"
                            title="Copy Game ID"
                            leftIcon={<Icon as={FaCopy} />}
                        >
                            {hasCopied ? "Copied!" : ""}
                        </Button>
                    </HStack>
                </HStack>
            </VStack>
        </Box>
    )
}

export default GameInfo