import React from 'react'
import { Grid, GridItem, Box, Text } from '@chakra-ui/react'
// import Cell from './Cell'

const Board = ({ boardData }) => { // boardData will be a 2D array
    if (!boardData || boardData.length === 0) {
        return <Text>Loading board...</Text>
    }

    const rows = boardData.length
    const cols = boardData[0]?.length || 0

    return (
        <Box display="flex" justifyContent="center" alignItems="center" my={4}>
            <Grid
                templateRows={`repeat(${rows}, 1fr)`}
                templateColumns={`repeat(${cols}, 1fr)`}
                gap={1}
                borderWidth="2px"
                borderColor="gray.400"
                p={1}
                bg="gray.100"
                width={`${cols * 50 + (cols - 1) * 4 + 4}px`} // Adjust size as needed (50px cell, 4px gap)
                height={`${rows * 50 + (rows - 1) * 4 + 4}px`}
            >
                {boardData.map((row, rowIndex) =>
                    row.map((cell, colIndex) => (
                        <GridItem
                            key={`${rowIndex}-${colIndex}`}
                            w="50px"
                            h="50px"
                            bg={cell ? (cell === 'X' ? 'red.300' : 'blue.300') : 'gray.200'}
                            display="flex"
                            justifyContent="center"
                            alignItems="center"
                            fontSize="2xl"
                            fontWeight="bold"
                            borderRadius="md"
                            borderWidth="1px"
                            borderColor="gray.300"
                        >
                            {/* <Cell value={cell} /> */}
                            {cell || ''}
                        </GridItem>
                    ))
                )}
            </Grid>
        </Box>
    )
}

export default Board