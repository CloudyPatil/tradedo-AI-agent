// E:\tradedo\app\frontend\components\common\error-boundary.tsx

"use client";

import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="text-center max-w-md p-8 bg-card border border-bear/30 rounded-lg corner-brackets">
            <AlertTriangle className="mx-auto text-bear mb-4" size={48} />
            <h1 className="text-2xl font-bold mb-2">Something went wrong</h1>
            <p className="text-sm text-muted-foreground mb-6">
              An unexpected error occurred. Please refresh the page.
            </p>
            <div className="space-y-2">
              <Button 
                onClick={() => window.location.reload()}
                className="bg-brand hover:bg-brand-500"
              >
                <RefreshCw size={14} className="mr-2" />
                REFRESH PAGE
              </Button>
              <Button 
                variant="outline"
                onClick={() => this.setState({ hasError: false })}
                className="w-full"
              >
                TRY AGAIN
              </Button>
            </div>
            
            {process.env.NODE_ENV === "development" && this.state.error && (
              <details className="mt-4 text-left">
                <summary className="text-xs cursor-pointer text-muted-foreground">
                  Error details (dev only)
                </summary>
                <pre className="mt-2 text-[10px] bg-secondary p-2 rounded overflow-auto max-h-40">
                  {this.state.error.stack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}