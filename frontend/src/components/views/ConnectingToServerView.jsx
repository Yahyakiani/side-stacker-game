// src/components/views/ConnectingToServerView.jsx
import React from 'react';
import { Container, VStack, Spinner, Text } from '@chakra-ui/react';

const ConnectingToServerView = () => {
    return (
        <Container centerContent py={{ base: "20vh", md: "30vh" }}>
            <VStack spacing={4}>
                <Spinner
                    thickness="4px"
                    speed="0.65s"
                    emptyColor="gray.200"
                    color="teal.500"
                    size="xl"
                />
                <Text fontSize="lg" color="gray.600">Connecting to server...</Text>
            </VStack>
        </Container>
    );
};

export default ConnectingToServerView;