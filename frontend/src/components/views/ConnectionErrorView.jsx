// src/components/views/ConnectionErrorView.jsx
import React from 'react';
import { Container, VStack, Heading, Text, Button } from '@chakra-ui/react';

const ConnectionErrorView = ({ errorMessage }) => {
    return (
        <Container centerContent py={{ base: "20vh", md: "30vh" }}>
            <VStack spacing={4} p={6} borderWidth="1px" borderRadius="lg" shadow="md" bg="white">
                <Heading color="red.500" size="lg">Connection Error</Heading>
                <Text color="gray.700" textAlign="center">{errorMessage || "An unknown connection error occurred."}</Text>
                <Text mt={2} fontSize="sm" color="gray.500">
                    Please ensure the backend server is running and try refreshing the page.
                </Text>
                <Button colorScheme="teal" onClick={() => window.location.reload()} mt={4}>
                    Refresh Page
                </Button>
            </VStack>
        </Container>
    );
};

export default ConnectionErrorView;