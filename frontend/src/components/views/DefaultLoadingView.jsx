// src/components/views/DefaultLoadingView.jsx
import React from 'react';
import { Container, VStack, Spinner, Text } from '@chakra-ui/react';

const DefaultLoadingView = ({ message = "Loading Game..." }) => {
    return (
        <Container centerContent py={10}>
            <VStack spacing={4}>
                <Spinner label={message} />
                <Text>{message}</Text>
                <Text fontSize="sm" color="gray.500">Please wait a moment.</Text>
            </VStack>
        </Container>
    );
};

export default DefaultLoadingView;