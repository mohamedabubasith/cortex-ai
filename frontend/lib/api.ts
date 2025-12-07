// API Configuration
import config from './config';
import axios from "axios";

const API_URL = config.apiV1Url;

const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Fix for multipart/form-data: Remove Content-Type to let browser set boundary
    if (config.data instanceof FormData) {
        delete config.headers["Content-Type"];
    }
    
    return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized
            localStorage.removeItem("token");
            window.location.href = "/login";
        }
        return Promise.reject(error);
    }
);

export default api;
