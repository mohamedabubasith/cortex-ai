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
                    "block text-sm font-medium mb-1",
                    isDark ? "text-gray-300" : "text-gray-700",
                    className
                )}
                {...props}
            />
        );
    }
);

Label.displayName = "Label";

export { Label };
