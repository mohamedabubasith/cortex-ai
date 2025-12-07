"use client";

import { Component, ReactNode } from "react";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: any) {
        console.error("Error boundary caught:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                this.props.fallback || (
                    <div className="min-h-screen flex items-center justify-center bg-black">
                        <div className="bg-nvidia-dark/80 backdrop-blur-sm border border-red-500/30 rounded-2xl p-8 max-w-md">
                            <h2 className="text-2xl font-bold text-white mb-4">Something went wrong</h2>
                            <p className="text-gray-400 mb-6">
                                {this.state.error?.message || "An unexpected error occurred"}
                            </p>
                            <button
                                onClick={() => this.setState({ hasError: false, error: undefined })}
                                className="w-full bg-nvidia-green text-black font-bold py-3 px-6 rounded-lg hover:bg-[#8CD600] transition-all"
                            >
                                Try Again
                            </button>
                        </div>
                    </div>
                )
            );
        }

        return this.props.children;
    }
}
