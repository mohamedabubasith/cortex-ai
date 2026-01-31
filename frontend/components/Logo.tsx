import React from "react";
import Image from "next/image";

interface LogoProps {
    className?: string;
    size?: "sm" | "md" | "lg" | "xl";
}

export default function Logo({ className = "", size = "md" }: LogoProps) {
    const sizeMap = {
        sm: 32,
        md: 48,
        lg: 64,
        xl: 96
    };

    return (
        <div className={`relative rounded-lg overflow-hidden ${className}`} style={{ width: sizeMap[size], height: sizeMap[size] }}>
            <Image
                src="/logo-basivo-v3.png"
                alt="Basivo Logo"
                fill
                className="object-cover"
            />
        </div>
    );
}
