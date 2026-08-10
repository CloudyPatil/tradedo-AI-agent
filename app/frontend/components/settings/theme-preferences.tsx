// E:\tradedo\app\frontend\components\settings\theme-preferences.tsx

"use client";

import { useTheme } from "next-themes";
import { Palette, Moon, Sun, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

export function ThemePreferences() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  const themes = [
    { key: "light", label: "Light", icon: Sun, description: "Warm cream background" },
    { key: "dark", label: "Dark", icon: Moon, description: "Terminal black" },
  ];

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center gap-2 mb-4">
        <Palette size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">APPEARANCE</h3>
      </div>

      <p className="text-xs text-muted-foreground mb-4">
        Choose your preferred theme for the trading terminal
      </p>

      <div className="grid grid-cols-2 gap-4">
        {themes.map(t => {
          const Icon = t.icon;
          const isActive = theme === t.key;
          
          return (
            <button
              key={t.key}
              onClick={() => setTheme(t.key)}
              className={cn(
                "p-6 rounded-lg border-2 transition-all text-left",
                isActive
                  ? "border-brand bg-brand/10 shadow-lg shadow-brand/10"
                  : "border-border hover:border-muted-foreground/30"
              )}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className={cn(
                  "w-12 h-12 rounded-lg flex items-center justify-center",
                  isActive ? "bg-brand text-white" : "bg-secondary text-muted-foreground"
                )}>
                  <Icon size={24} />
                </div>
                
                <div>
                  <p className={cn(
                    "font-bold text-lg",
                    isActive && "text-brand"
                  )}>
                    {t.label}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {t.description}
                  </p>
                </div>
                
                {isActive && (
                  <div className="ml-auto">
                    <div className="w-3 h-3 rounded-full bg-brand animate-pulse" />
                  </div>
                )}
              </div>
              
              <p className="text-[10px] text-muted-foreground">
                {isActive ? "✓ CURRENTLY ACTIVE" : "Click to activate"}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}