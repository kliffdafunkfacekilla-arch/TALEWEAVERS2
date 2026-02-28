import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

interface Props {
    children?: ReactNode;
}

interface State {
    hasError: boolean;
    errorMsg: string;
    errorStack: string;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        errorMsg: "",
        errorStack: ""
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, errorMsg: error.message, errorStack: error.stack || "" };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div style={{ backgroundColor: 'black', color: 'red', padding: '2rem', height: '100vh', width: '100vw', fontFamily: 'monospace' }}>
                    <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#ff4444' }}>VTT UI Crash Trapped</h1>
                    <h2 style={{ fontSize: '1.2rem', color: 'white' }}>{this.state.errorMsg}</h2>
                    <pre style={{ marginTop: '2rem', color: '#aaaaaa', whiteSpace: 'pre-wrap' }}>{this.state.errorStack}</pre>
                </div>
            );
        }

        return this.props.children;
    }
}
