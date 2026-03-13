import { LabelHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";

const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
    ({ className, ...props }, ref) => {
        const { theme } = useTheme();
        const isDark = theme === "dark";

        return (
            <label
                ref={ref}
                className={cn(
                    "block text-xs font-bold uppercase tracking-wider mb-1.5 ml-1",
                    isDark ? "text-gray-400" : "text-gray-500",
                    className
                )}
                {...props}
            />
        );
    }
);

Label.displayName = "Label";

export { Label };
