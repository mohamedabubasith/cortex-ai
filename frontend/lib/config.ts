/**
 * API Configuration
 * Reads from environment variables with fallback to localhost for development
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const config = {
    apiUrl: API_BASE_URL,
    apiV1Url: `${API_BASE_URL}/api/v1`,
};

export default config;
