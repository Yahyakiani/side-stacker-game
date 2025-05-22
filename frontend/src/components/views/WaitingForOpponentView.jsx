// src/components/views/WaitingForOpponentView.jsx
import React from 'react';
import { Container, VStack, Heading, Text, HStack, Input, IconButton, Spinner, useToast } from '@chakra-ui/react';
import { FaCopy } from 'react-icons/fa';

const WaitingForOpponentView = ({ gameId }) => {
    const toast = useToast();

    const handleCopyGameId = () => {
        if (gameId) {
            navigator.clipboard.writeText(gameId);
            toast({ title: "Game ID Copied!", status: "success", duration: 2000, isClosable: true });
        }
    };

    return (
        <Container maxW="container.md" py={10} textAlign="center">
            <VStack spacing={6}>
                <Heading as="h2" size="lg" color="teal.500">Waiting for Opponent...</Heading>
                <Text fontSize="lg">Share this Game ID with your friend:</Text>
                <HStack justifyContent="center">
                    <Input
                        value={gameId || "Loading ID..."}
                        isReadOnly
                        pr="4.5rem"
                        textAlign="center"
                        fontSize="xl"
                        fontFamily="monospace"
                        w="auto"
                        minW="300px"
                    />
                    <IconButton
                        aria-label="Copy Game ID"
                        icon={<FaCopy />}
                        colorScheme="teal"
                        onClick={handleCopyGameId}
                        isDisabled={!gameId}
                    />
                </HStack>
                <Spinner label="Waiting for P2..." thickness="4px" speed="0.65s" color="teal.500" size="lg" mt={4} />
            </VStack>
        </Container>
    );
};

export default WaitingForOpponentView;