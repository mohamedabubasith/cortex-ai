"use client";

import { useEffect, useRef } from "react";
// @ts-ignore

export default function TubesBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (!canvasRef.current) return;

        let cursor: any;

        const init = async () => {
            try {
                // Dynamically import to avoid SSR issues
                // @ts-ignore
                const { Tubes1Cursor } = await import("threejs-components");

                if (!canvasRef.current) return;

                // Tubes1Cursor is a factory function, not a class
                // Arguments: (element, options)
                cursor = Tubes1Cursor(canvasRef.current, {
                    gpgpuSize: 512,
                    colors: [0x76b900, 0x000000], // NVIDIA Green and Black
                    color: 0x76b900,
                    coordScale: 0.5,
                    noiseIntensity: 0.001,
                    noiseTimeCoef: 0.0001,
                    pointSize: 2,
                    pointDecay: 0.0025,
                    sleepRadiusX: 250,
                    sleepRadiusY: 250,
                    sleepTimeCoefX: 0.001,
                    sleepTimeCoefY: 0.002
                });
            } catch (e) {
                console.error("Failed to initialize TubesCursor", e);
            }
        };

        init();

        return () => {
            if (cursor && cursor.dispose) {
                cursor.dispose();
            }
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 z-0 pointer-events-none w-full h-full"
            style={{ opacity: 0.6 }}
        />
    );
}
