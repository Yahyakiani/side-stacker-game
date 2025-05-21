import { Grid, GridItem, Box, Text, useColorModeValue } from '@chakra-ui/react'


const Board = ({ boardData }) => { // boardData will be a 2D array

    const cellBg = useColorModeValue('gray.100', 'gray.700') // Background for empty cells
    const cellBorderColor = useColorModeValue('gray.300', 'gray.600')
    const boardBorderColor = useColorModeValue('gray.400', 'gray.500')

    // Piece colors using the theme (adjust theme in main.jsx if needed)
    const xColor = useColorModeValue('red.500', 'playerX.500')
    const oColor = useColorModeValue('blue.500', 'playerO.500')
    const pieceTextColor = useColorModeValue('white', 'playerX.text')


    if (!boardData || boardData.length === 0) {
        return <Text>Loading board...</Text>
    }

    const rows = boardData.length
    const cols = boardData[0]?.length || 0
    const cellSize = "50px" // Define cell size
    const gapSize = "2px"    // Define gap size

    return (
        <Box display="flex" justifyContent="center" alignItems="center" my={4}>
            <Grid
                templateRows={`repeat(${rows}, ${cellSize})`}
                templateColumns={`repeat(${cols}, ${cellSize})`}
                gap={gapSize} // Use a small gap
                borderWidth="2px"
                borderColor={boardBorderColor} // Border for the whole grid
                borderRadius="lg" // Rounded corners for the grid
                p="4px" // Padding inside the grid, around cells
                bg={useColorModeValue('gray.200', 'gray.900')} // Background for the grid container itself
                shadow="md"
            >
                {boardData.map((row, rowIndex) =>
                    row.map((cell, colIndex) => (
                        <GridItem
                            key={`${rowIndex}-${colIndex}`}
                            w={cellSize}
                            h={cellSize}
                            bg={cell ? (cell === 'X' ? xColor : oColor) : cellBg}
                            color={cell ? pieceTextColor : 'inherit'} // Text color for X/O
                            display="flex"
                            justifyContent="center"
                            alignItems="center"
                            fontSize="2xl"
                            fontWeight="bold"
                            borderRadius="md" // Rounded cells
                            // No border on individual cells to avoid overlap with gap
                            // If you want cell borders, consider outline or box-shadow
                            // Example: boxShadow="inset 0 0 0 1px gray.600" for dark mode
                            _hover={{ // Subtle hover for empty cells if needed (for future move indication)
                                bg: !cell ? (useColorModeValue('gray.200', 'gray.600')) : undefined,
                                cursor: !cell ? 'pointer' : 'default'
                            }}
                        >
                            {cell || ''}
                        </GridItem>
                    ))
                )}
            </Grid>
        </Box>
    )
}

export default Board