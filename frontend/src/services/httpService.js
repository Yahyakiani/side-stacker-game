// frontend/src/services/httpService.js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'; // Ensure your .env has VITE_API_BASE_URL

export const fetchUserStats = async (username) => {
    if (!username || typeof username !== 'string' || username.trim() === '') {
        console.error('httpService: Username is required and must be a non-empty string to fetch stats.');
        // Optionally throw an error or return a specific error object
        // For now, returning null or an error structure
        return { success: false, error: 'Invalid username provided.' };
    }

    const encodedUsername = encodeURIComponent(username.trim());
    const url = `${API_BASE_URL}/users/${encodedUsername}/stats`;
    console.log(`httpService: Fetching stats for ${username} from ${url}`);

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                // Add other headers like Authorization if you implement auth later
            },
        });

        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json(); // Try to parse error response from API
            } catch (e) {
                errorData = { message: `HTTP error ${response.status}: ${response.statusText}` };
            }
            console.error(`httpService: Error fetching stats for ${username}. Status: ${response.status}`, errorData);
            return { success: false, error: errorData.detail || errorData.message || `Failed to fetch stats (${response.status})` };
        }

        const statsData = await response.json();
        console.log(`httpService: Successfully fetched stats for ${username}:`, statsData);
        return { success: true, data: statsData };

    } catch (error) {
        console.error(`httpService: Network or other error fetching stats for ${username}:`, error);
        return { success: false, error: error.message || 'Network error or an unexpected issue occurred.' };
    }
};