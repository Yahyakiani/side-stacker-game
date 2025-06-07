// frontend/src/components/GameHistoryStats.jsx
// ### NEW FILE ###
import React from 'react';
import { Box, Text, Stat, StatLabel, StatNumber, StatHelpText, SimpleGrid, Heading, Spinner, Alert, AlertIcon, VStack } from '@chakra-ui/react';

const GameHistoryStats = ({ username, stats, isLoading, error }) => {
    if (!username) {
        return ( // Optionally render nothing or a prompt if no username is set yet
            <Box p={4} borderWidth="1px" borderRadius="lg" shadow="sm" bg="gray.700" mt={4}>
                <Text textAlign="center" color="gray.400">Enter a username in Game Setup to see your stats.</Text>
            </Box>
        );
    }

    if (isLoading) {
        return (
            <Box p={4} borderWidth="1px" borderRadius="lg" shadow="sm" bg="gray.700" mt={4} textAlign="center">
                <Spinner thickness="3px" speed="0.65s" emptyColor="gray.600" color="teal.300" size="lg" />
                <Text mt={2} color="gray.300">Loading stats for {username}...</Text>
            </Box>
        );
    }

    if (error) {
        return (
            <Box p={4} borderWidth="1px" borderRadius="lg" shadow="sm" bg="gray.700" mt={4}>
                <Alert status="error" borderRadius="md">
                    <AlertIcon />
                    <Text color="red.200">Error loading stats: {String(error)}</Text>
                </Alert>
            </Box>
        );
    }

    // Ensure stats object has all expected fields, defaulting to 0 if not present
    const displayStats = {
        games_played: stats?.games_played ?? 0,
        wins: stats?.wins ?? 0,
        losses: stats?.losses ?? 0,
        draws: stats?.draws ?? 0,
        abandoned_by_user: stats?.abandoned_by_user ?? 0,
    };


    return (
        <Box p={4} borderWidth="1px" borderRadius="lg" shadow="sm" bg="gray.700" color="whiteAlpha.900" mt={4}>
            <Heading size="md" textAlign="center" mb={4} color="teal.300">
                Stats for: <Text as="span" color="whiteAlpha.800" fontWeight="bold">{username}</Text>
            </Heading>
            <SimpleGrid columns={{ base: 2, md: 3 }} spacing={4}>
                <Stat>
                    <StatLabel color="gray.400">Games Played</StatLabel>
                    <StatNumber>{displayStats.games_played}</StatNumber>
                </Stat>
                <Stat>
                    <StatLabel color="green.300">Wins</StatLabel>
                    <StatNumber color="green.300">{displayStats.wins}</StatNumber>
                </Stat>
                <Stat>
                    <StatLabel color="red.300">Losses</StatLabel>
                    <StatNumber color="red.300">{displayStats.losses}</StatNumber>
                </Stat>
                <Stat>
                    <StatLabel color="yellow.300">Draws</StatLabel>
                    <StatNumber color="yellow.300">{displayStats.draws}</StatNumber>
                </Stat>
                <Stat>
                    <StatLabel color="orange.300">Abandoned</StatLabel>
                    <StatNumber color="orange.300">{displayStats.abandoned_by_user}</StatNumber>
                </Stat>
            </SimpleGrid>
        </Box>
    );
};

export default GameHistoryStats;