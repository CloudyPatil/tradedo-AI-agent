// E:\tradedo\app\frontend\components\common\command-palette.tsx

"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "cmdk";
import {
  LayoutDashboard, Sparkles, Bot, Wallet, Target,
  BarChart3, Shield, Settings, TrendingUp, Search,
  Play, StopCircle, Sun, Moon,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { tradeoAPI } from "@/lib/api/client";
import { toast } from "sonner";

const POPULAR_STOCKS = [
  "RELIANCE", "TCS", "HDFCBANK", "INFY", "WIPRO",
  "TATAMOTORS", "SBIN", "ICICIBANK", "SUNPHARMA", "BAJFINANCE",
];

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();
  const { setTheme } = useTheme();
  const queryClient = useQueryClient();

  // Keyboard shortcut: Cmd+K / Ctrl+K
  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const startAgent = useMutation({
    mutationFn: tradeoAPI.startAgent,
    onSuccess: () => {
      toast.success("Agent started!");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
  });

  const stopAgent = useMutation({
    mutationFn: tradeoAPI.stopAgent,
    onSuccess: () => {
      toast.success("Agent stopped!");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
  });

  const runCommand = (fn: () => void) => {
    setOpen(false);
    fn();
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <div className="border border-border rounded-lg bg-card overflow-hidden max-w-2xl mx-auto">
        <CommandInput
          placeholder="Search commands, stocks, pages..."
          className="w-full px-4 py-3 border-b border-border bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
        <CommandList className="max-h-96 overflow-y-auto p-2">
          <CommandEmpty className="py-6 text-center text-sm text-muted-foreground">
            No results found.
          </CommandEmpty>

          <CommandGroup heading="Navigation">
            <CommandItem 
              onSelect={() => runCommand(() => router.push("/"))}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <LayoutDashboard size={14} /> Dashboard
            </CommandItem>
            <CommandItem 
              onSelect={() => runCommand(() => router.push("/signals"))}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <Sparkles size={14} /> AI Signals
            </CommandItem>
            <CommandItem 
              onSelect={() => runCommand(() => router.push("/agent"))}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <Bot size={14} /> Autonomous Agent
            </CommandItem>
            <CommandItem 
              onSelect={() => runCommand(() => router.push("/trades"))}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <Target size={14} /> Trades History
            </CommandItem>
            <CommandItem 
              onSelect={() => runCommand(() => router.push("/analytics"))}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <BarChart3 size={14} /> Analytics
            </CommandItem>
            <CommandItem 
              onSelect={() => runCommand(() => router.push("/risk"))}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <Shield size={14} /> Risk Dashboard
            </CommandItem>
            <CommandItem 
              onSelect={() => runCommand(() => router.push("/settings"))}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <Settings size={14} /> Settings
            </CommandItem>
          </CommandGroup>

          <CommandSeparator className="my-2 h-px bg-border" />

          <CommandGroup heading="Quick Stocks">
            {POPULAR_STOCKS.map(s => (
              <CommandItem
                key={s}
                onSelect={() => runCommand(() => router.push(`/stock/${s}`))}
                className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
              >
                <TrendingUp size={14} className="text-brand" /> 
                <span className="font-mono">{s}</span>
                <span className="ml-auto text-xs text-muted-foreground">Analyze →</span>
              </CommandItem>
            ))}
          </CommandGroup>

          <CommandSeparator className="my-2 h-px bg-border" />

          <CommandGroup heading="Agent Actions">
            <CommandItem
              onSelect={() => runCommand(() => startAgent.mutate())}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <Play size={14} className="text-bull" /> Start Agent
            </CommandItem>
            <CommandItem
              onSelect={() => runCommand(() => stopAgent.mutate())}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <StopCircle size={14} className="text-bear" /> Stop Agent
            </CommandItem>
          </CommandGroup>

          <CommandSeparator className="my-2 h-px bg-border" />

          <CommandGroup heading="Theme">
            <CommandItem
              onSelect={() => runCommand(() => setTheme("light"))}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <Sun size={14} /> Light Theme
            </CommandItem>
            <CommandItem
              onSelect={() => runCommand(() => setTheme("dark"))}
              className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent cursor-pointer text-sm"
            >
              <Moon size={14} /> Dark Theme
            </CommandItem>
          </CommandGroup>
        </CommandList>

        <div className="border-t border-border px-3 py-2 flex items-center justify-between text-[10px] text-muted-foreground">
          <span>Press <kbd className="px-1 py-0.5 rounded bg-secondary">⌘K</kbd> to open anytime</span>
          <span>ESC to close</span>
        </div>
      </div>
    </CommandDialog>
  );
}