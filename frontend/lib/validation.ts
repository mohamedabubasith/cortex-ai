export const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

export interface PasswordStrength {
    score: number; // 0-4
    label: string;
    color: string;
}

export const calculatePasswordStrength = (password: string): PasswordStrength => {
    let score = 0;
    if (!password) return { score: 0, label: "Weak", color: "bg-gray-600" };

    if (password.length > 6) score += 1;
    if (password.length > 10) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;

    // Cap at 4
    if (score > 4) score = 4;

    switch (score) {
        case 0:
        case 1:
            return { score, label: "Weak", color: "bg-red-500" };
        case 2:
            return { score, label: "Fair", color: "bg-yellow-500" };
        case 3:
            return { score, label: "Good", color: "bg-blue-500" };
        case 4:
            return { score, label: "Strong", color: "bg-green-500" };
        default:
            return { score: 0, label: "Weak", color: "bg-gray-600" };
    }
};
