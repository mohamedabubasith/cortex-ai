import { InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ className, label, error, ...props }, ref) => {
        const { theme } = useTheme();
        const isDark = theme === "dark";

        return (
            <div className="w-full">
                {label && (
                    <label className={cn("block text-xs font-bold uppercase tracking-wider mb-1.5 ml-1", isDark ? "text-gray-400" : "text-gray-500")}>
                        {label}
                    </label>
                )}
                <input
                    ref={ref}
                    className={cn(
                        "w-full border rounded-xl px-4 py-2.5 transition-all duration-200 outline-none",
                        isDark
                            ? "bg-black/40 border-white/10 text-white placeholder-gray-600 focus:bg-black/60 focus:border-nvidia-green/50 focus:ring-2 focus:ring-nvidia-green/20"
                            : "bg-white border-gray-200 text-gray-900 placeholder-gray-400 focus:border-nvidia-green focus:ring-2 focus:ring-nvidia-green/20",
                        error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20",
                        className
                    )}
                    {...props}
                />
                {error && <p className="text-xs text-red-500 mt-1.5 ml-1 font-medium">{error}</p>}
            </div>
        );
    }
);

Input.displayName = "Input";

export { Input };
