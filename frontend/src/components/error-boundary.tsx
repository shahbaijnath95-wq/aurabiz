"use client";

import { Component, ReactNode, ErrorInfo } from "react";

// ============================================================
// ERROR BOUNDARY — Catches and displays errors gracefully
// ============================================================

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    this.props.onError?.(error, errorInfo);
    console.error("[ErrorBoundary]", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = "/dashboard";
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-lg w-full text-center">
            {/* Error Icon */}
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-50 flex items-center justify-center">
              <span className="text-4xl">⚠️</span>
            </div>

            {/* Error Message */}
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Kuch gadbad ho gayi!
            </h2>
            <p className="text-gray-500 mb-2">
              Page load nahi ho paya. Chinta mat karo, aapka data safe hai.
            </p>

            {/* Error Details (collapsible) */}
            {this.state.error && (
              <details className="mt-4 mb-6 text-left">
                <summary className="text-sm text-gray-400 cursor-pointer hover:text-gray-600">
                  Technical details
                </summary>
                <div className="mt-2 p-3 bg-gray-50 rounded-lg text-xs font-mono text-gray-600 overflow-auto max-h-32">
                  <p className="font-bold">{this.state.error.name}: {this.state.error.message}</p>
                  {this.state.errorInfo && (
                    <pre className="mt-2 whitespace-pre-wrap">
                      {this.state.errorInfo.componentStack?.slice(0, 500)}
                    </pre>
                  )}
                </div>
              </details>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="px-5 py-2.5 bg-amber-500 text-white rounded-xl font-medium hover:bg-amber-600 transition-colors"
              >
                Try karein
              </button>
              <button
                onClick={this.handleReload}
                className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
              >
                Page refresh
              </button>
              <button
                onClick={this.handleGoHome}
                className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
              >
                Dashboard jao
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// ============================================================
// PAGE ERROR FALLBACK — Simpler inline error display
// ============================================================

interface PageErrorProps {
  error?: string;
  onRetry?: () => void;
}

export function PageError({ error = "Data load nahi ho paya", onRetry }: PageErrorProps) {
  return (
    <div className="min-h-[300px] flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-50 flex items-center justify-center">
          <span className="text-2xl">😕</span>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-1">{error}</h3>
        <p className="text-sm text-gray-500 mb-4">
          Backend chal raha hai kya? Refresh karein ya dobara try karein.
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-amber-500 text-white rounded-lg font-medium hover:bg-amber-600 transition-colors"
          >
            Retry karein
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================================
// INLINE ERROR — Small error display for sections
// ============================================================

export function InlineError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-red-50 border border-red-100 rounded-lg">
      <span className="text-red-500">⚠️</span>
      <p className="text-sm text-red-700 flex-1">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs text-red-600 hover:text-red-800 font-medium"
        >
          Retry
        </button>
      )}
    </div>
  );
}
