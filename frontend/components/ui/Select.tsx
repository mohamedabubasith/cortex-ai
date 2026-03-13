import { SelectHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
    label?: string;
    error?: string;
    options?: { label: string; value: string | number }[];
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
    ({ className, label, error, children, options, ...props }, ref) => {
        const { theme } = useTheme();
        const isDark = theme === "dark";

        return (
            <div className="w-full">
                {label && (
                    <label className={cn("block text-xs font-bold uppercase tracking-wider mb-1.5 ml-1", isDark ? "text-gray-400" : "text-gray-500")}>
                        {label}
                    </label>
                )}
                <select
                    ref={ref}
                    className={cn(
                        "w-full border rounded-xl px-3.5 py-3 text-base sm:py-2.5 sm:text-sm transition-all duration-200 outline-none appearance-none cursor-pointer",
                        isDark
                            ? "bg-black/40 border-white/10 text-white focus:bg-black/60 focus:border-nvidia-green/50 focus:ring-2 focus:ring-nvidia-green/20"
                            : "bg-white border-gray-200 text-gray-900 focus:border-nvidia-green focus:ring-2 focus:ring-nvidia-green/20",
                        error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20",
                        className
                    )}
                    {...props}
                >
                    {options
                        ? options.map((opt) => (
                            <option key={opt.value} value={opt.value} className={isDark ? "bg-gray-900" : "bg-white"}>
                                {opt.label}
                            </option>
                        ))
                        : children}
                </select>
                {error && <p className="text-xs text-red-500 mt-1.5 ml-1 font-medium">{error}</p>}
            </div>
        );
    }
);

Select.displayName = "Select";

export { Select };
