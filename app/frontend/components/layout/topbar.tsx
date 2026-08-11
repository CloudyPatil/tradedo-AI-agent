// E:\tradedo\app\frontend\components\layout\topbar.tsx

"use client";

import * as React from "react";
import { Crosshair } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import { formatTime, formatDate } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Topbar() {
  const [time, setTime] = React.useState<Date | null>(null);

  React.useEffect(() => {
    // Set initial time on client
    setTime(new Date());
    
    // Update every second
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="border-b border-border bg-card">
      <div className="h-16 px-6 flex items-center justify-between">
        
        {/* Left: System Info */}
        <div className="flex items-center gap-8">
          <div className="text-xs">
            <p className="text-muted-foreground tracking-wider">SYSTEM</p>
            <p className="text-brand font-mono font-bold">AI TRADING TERMINAL</p>
          </div>
          
          <div className="text-xs">
            <p className="text-muted-foreground tracking-wider">VERSION</p>
            <p className="font-mono font-bold">2.0.0</p>
          </div>
        </div>

        {/* Center: Coordinates */}
        <div className="flex items-center gap-3 text-xs font-mono text-muted-foreground">
          <Crosshair size={14} className="text-brand" />
          <div>
            <p>NSE / BSE</p>
            <p>MUMBAI, IN</p>
          </div>
        </div>

        {/* Right: Time + Theme + User */}
        <div className="flex items-center gap-6">
            {/* NEW: Search Command Button */}
            <button 
              onClick={() => {
                const event = new KeyboardEvent("keydown", {
                  key: "k",
                  metaKey: true,
                  ctrlKey: true,
                });
                document.dispatchEvent(event);
              }}
              className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border bg-secondary/50 hover:bg-accent transition-colors text-xs text-muted-foreground"
            >
              <Search size={14} />
              <span>Search...</span>
              <kbd className="ml-4 px-1.5 py-0.5 text-[10px] font-mono rounded bg-background border border-border">
                ⌘K
              </kbd>
            </button>

          <div className="text-xs font-mono text-right">
            <p className="text-foreground font-bold tabular-nums min-w-[80px]">
              {time ? formatTime(time) : "--:--:--"}
            </p>
            <p className="text-muted-foreground">
              {time ? formatDate(time) : "-- --- ----"}
            </p>
          </div>

          <ThemeToggle />

          <Avatar className="w-9 h-9 border-2 border-brand">
            <AvatarFallback className="bg-brand text-white text-xs font-bold">
              TD
            </AvatarFallback>
          </Avatar>
        </div>
      </div>

      <div className="h-0.5 bg-gradient-to-r from-transparent via-brand to-transparent opacity-50" />
    </header>
  );
}