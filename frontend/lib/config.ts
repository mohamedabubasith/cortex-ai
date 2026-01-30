/**
 * API Configuration
 * Reads from environment variables with fallback to localhost for development
 */

// Use relative path so requests go through Next.js proxy (port 3000)
// V2: Force relative path and log for verification
if (typeof window !== 'undefined') {
    console.log('[[CONFIG_DEBUG]] API_BASE_URL is explicitly empty string. Protocol should be relative.');
}
const API_BASE_URL = '';

export const config = {
    apiUrl: API_BASE_URL,
    apiV1Url: `${API_BASE_URL}/api/v1`,
};

export default config;
