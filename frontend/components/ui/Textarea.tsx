import { TextareaHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
    label?: string;
    error?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, label, error, ...props }, ref) => {
        const { theme } = useTheme();
        const isDark = theme === "dark";

        return (
            <div className="w-full">
                {label && (
                    <label className={cn("block text-sm font-medium mb-1", isDark ? "text-gray-300" : "text-gray-700")}>
                        {label}
                    </label>
                )}
                <textarea
                    ref={ref}
                    className={cn(
                        "w-full border rounded-lg px-4 py-2 focus:ring-nvidia-green focus:border-nvidia-green transition-colors focus:outline-none scrollbar-thin",
                        isDark
                            ? "bg-black/50 border-gray-700 text-white placeholder-gray-600 focus:bg-black/70"
                            : "bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-nvidia-green",
                        error && "border-red-500 focus:ring-red-500 focus:border-red-500",
                        className
                    )}
                    {...props}
                />
                {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
            </div>
        );
    }
);

Textarea.displayName = "Textarea";

export { Textarea };
