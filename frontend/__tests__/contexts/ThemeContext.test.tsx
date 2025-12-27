import { renderHook, act } from '@testing-library/react';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';

// Mock localStorage
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: (key: string) => store[key] || null,
        setItem: (key: string, value: string) => {
            store[key] = value.toString();
        },
        removeItem: (key: string) => {
            delete store[key];
        },
        clear: () => {
            store = {};
        }
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock
});

describe('ThemeContext', () => {
    beforeEach(() => {
        localStorage.clear();
        document.documentElement.classList.remove('light', 'dark');
    });

    it('should provide default dark theme', () => {
        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider
        });

        expect(result.current.theme).toBe('dark');
    });

    it('should toggle theme from dark to light', () => {
        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider
        });

        act(() => {
            result.current.toggleTheme();
        });

        expect(result.current.theme).toBe('light');
    });

    it('should toggle theme from light to dark', () => {
        localStorage.setItem('theme', 'light');

        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider
        });

        act(() => {
            result.current.toggleTheme();
        });

        expect(result.current.theme).toBe('dark');
    });

    it('should persist theme to localStorage', () => {
        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider
        });

        act(() => {
            result.current.setTheme('light');
        });

        expect(localStorage.getItem('theme')).toBe('light');
    });

    it('should load theme from localStorage on mount', () => {
        localStorage.setItem('theme', 'light');

        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider
        });

        expect(result.current.theme).toBe('light');
    });

    it('should apply theme class to document element', () => {
        const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider
        });

        act(() => {
            result.current.setTheme('light');
        });

        expect(document.documentElement.classList.contains('light')).toBe(true);
        expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('should throw error when useTheme is used outside ThemeProvider', () => {
        // Suppress console.error for this test
        const originalError = console.error;
        console.error = jest.fn();

        expect(() => {
            renderHook(() => useTheme());
        }).toThrow('useTheme must be used within a ThemeProvider');

        console.error = originalError;
    });
});
