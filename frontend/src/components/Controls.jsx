// frontend/src/components/Controls.jsx
import React from 'react'
import { Box, Button, VStack, HStack, Text, Icon } from '@chakra-ui/react'
import { FaArrowLeft, FaArrowRight } from 'react-icons/fa' // For arrow icons
import { NUM_ROWS } from '../constants/gameConstants' // Assuming NUM_ROWS is defined in your constants

const Controls = ({ onMakeMove, isDisabled, currentPlayerPiece }) => {
    const handleMove = (rowIndex, side) => {
        if (!isDisabled) {
            onMakeMove(rowIndex, side)
        }
    }

    return (
        <VStack spacing={2} align="stretch" my={4}>
            <Text textAlign="center" fontWeight="bold" mb={2}>
                Click a side to place your piece ({currentPlayerPiece || '?'})
            </Text>
            {Array.from({ length: NUM_ROWS }).map((_, rowIndex) => (
                <HStack key={rowIndex} spacing={2} justifyContent="center">
                    <Button
                        onClick={() => handleMove(rowIndex, 'L')}
                        isDisabled={isDisabled}
                        leftIcon={<Icon as={FaArrowLeft} />}
                        colorScheme="green"
                        variant="outline"
                        size="sm"
                        w="100px" // Fixed width for alignment
                    >
                        Row {rowIndex}
                    </Button>
                    <Box
                        w={`${50 * 7 + (7 - 1) * 4}px`} // Approximate width of the board for visual spacing
                        textAlign="center"
                        fontWeight="bold"
                        p={2}
                        borderWidth="1px"
                        borderColor="transparent" // Keep space but no visible border
                    >
                        {/* Could display row number here too or leave empty */}
                    </Box>
                    <Button
                        onClick={() => handleMove(rowIndex, 'R')}
                        isDisabled={isDisabled}
                        rightIcon={<Icon as={FaArrowRight} />}
                        colorScheme="blue"
                        variant="outline"
                        size="sm"
                        w="100px" // Fixed width for alignment
                    >
                        Row {rowIndex}
                    </Button>
                </HStack>
            ))}
        </VStack>
    )
}

export default Controls