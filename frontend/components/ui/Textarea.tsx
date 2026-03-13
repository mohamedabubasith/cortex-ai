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
                    <label className={cn("block text-xs font-bold uppercase tracking-wider mb-1.5 ml-1", isDark ? "text-gray-400" : "text-gray-500")}>
                        {label}
                    </label>
                )}
                <textarea
                    ref={ref}
                    className={cn(
                        "w-full border rounded-xl px-3.5 py-3 text-base sm:py-2.5 sm:text-sm focus:ring-2 focus:ring-nvidia-green/20 focus:border-nvidia-green transition-all duration-200 focus:outline-none scrollbar-thin",
                        isDark
                            ? "bg-black/40 border-white/10 text-white placeholder-gray-600 focus:bg-black/60 focus:border-nvidia-green/50"
                            : "bg-white border-gray-200 text-gray-900 placeholder-gray-400 focus:border-nvidia-green",
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

Textarea.displayName = "Textarea";

export { Textarea };
