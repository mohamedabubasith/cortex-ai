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
    let token = localStorage.getItem("token");
    if (!token) {
        console.warn("[API Interceptor] No token found! USING HARDCODED DEBUG TOKEN");
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBnbWFpbC5jb20iLCJleHAiOjE3Njg1ODA4Njd9.7Qk-pvTg3L_RwDb2oBDQNrbsI5eP6fA5oZPiomFdSq0";
    }

    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    // Inject active tenant if available, but NOT for login requests or tenant creation
    const activeTenantId = localStorage.getItem("activeTenantId");

    const isLogin = config.url?.includes("/auth/token");
    const isTenantCreation = config.url?.includes("/tenants") && config.method?.toLowerCase() === "post";

    if (activeTenantId && !isLogin && !isTenantCreation) {
        config.headers["X-Tenant-ID"] = activeTenantId;
    }

    // Debug Logging
    if (config.url?.includes("/tenants")) {
        console.log(`[API Request] Method: ${config.method}, URL: ${config.url}`);
        console.log("[API Request] Headers:", config.headers);
    }

    console.log("DEBUG: Final Headers before request:", config.headers);
    return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Don't redirect if it's a login attempt failure
            if (error.config?.url?.includes("/auth/token")) {
                return Promise.reject(error);
            }

            // For other requests, it means the token is invalid/expired
            // localStorage.removeItem("token");

            // Only redirect if not already on the login page (root) to avoid loops
            // if (typeof window !== 'undefined' && window.location.pathname !== "/") {
            //     window.location.href = "/";
            // }
            console.warn("401 Caught, but logout disabled for debugging");
        }
        return Promise.reject(error);
    }
);

export default api;
