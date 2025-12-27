"use client";

import { useEffect, useRef } from "react";
// @ts-ignore
import { Tubes1Cursor } from "threejs-components";

export default function TubesBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (!canvasRef.current) return;

        let cursor: any;

        try {
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

        return () => {
            if (cursor && cursor.dispose) {
                cursor.dispose();
            }
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed top-0 left-0 z-0 pointer-events-none"
            style={{
                width: '100vw',
                height: '100vh',
                opacity: 0.6
            }}
        />
    );
}
