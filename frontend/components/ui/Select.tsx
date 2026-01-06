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
                    <label className={cn("block text-sm font-medium mb-1", isDark ? "text-gray-300" : "text-gray-700")}>
                        {label}
                    </label>
                )}
                <select
                    ref={ref}
                    className={cn(
                        "w-full border rounded-lg px-4 py-2 focus:ring-nvidia-green focus:border-nvidia-green transition-colors focus:outline-none appearance-none cursor-pointer",
                        isDark
                            ? "bg-black/50 border-gray-700 text-white focus:bg-black/70"
                            : "bg-white border-gray-300 text-gray-900 focus:border-nvidia-green",
                        error && "border-red-500 focus:ring-red-500 focus:border-red-500",
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
                {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
            </div>
        );
    }
);

Select.displayName = "Select";

export { Select };
