// E:\tradedo\app\frontend\components\layout\sidebar.tsx

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, TrendingUp, Sparkles, Wallet,
  Bot, Target, Search, BarChart3, FileText, Settings,
  Shield, Scan,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/",           label: "Dashboard",        icon: LayoutDashboard },
  { href: "/markets",    label: "Markets",          icon: TrendingUp },
  { href: "/screener",   label: "Screener",         icon: Scan },
  { href: "/signals",    label: "AI Signals",       icon: Sparkles },
  { href: "/portfolio",  label: "Portfolio",        icon: Wallet },
  { href: "/agent",      label: "Autonomous Agent", icon: Bot },
  { href: "/trades",     label: "Trades",           icon: Target },
  { href: "/analytics",  label: "Analytics",        icon: BarChart3 },
  { href: "/risk",       label: "Risk Dashboard",   icon: Shield },
  { href: "/reports",    label: "Reports",          icon: FileText },
  { href: "/settings",   label: "Settings",         icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 border-r border-border bg-card flex flex-col">
      {/* Logo */}
      <div className="p-5 border-b border-border">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-9 h-9 bg-brand rounded flex items-center justify-center text-white font-bold text-lg font-display">
            T
          </div>
          <div>
            <h1 className="text-lg font-bold font-display tracking-tight">
              TRADEDO
            </h1>
            <p className="text-[10px] text-muted-foreground tracking-wider uppercase">
              AI Trading Terminal
            </p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all",
                isActive
                  ? "bg-brand text-white shadow-lg shadow-brand/20"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Brand Message */}
      <div className="p-4 border-t border-border">
        <div className="space-y-1 text-xs">
          <p>
            <span className="text-muted-foreground">TRADE </span>
            <span className="text-brand font-bold">SMARTER.</span>
          </p>
          <p>
            <span className="text-muted-foreground">AUTOMATE </span>
            <span className="text-brand font-bold">BETTER.</span>
          </p>
          <p>
            <span className="text-muted-foreground">GROW </span>
            <span className="text-brand font-bold">FASTER.</span>
          </p>
        </div>
      </div>

      {/* Status */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2 text-xs">
          <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse" />
          <span className="text-muted-foreground">CONNECTED</span>
        </div>
        <p className="text-[10px] text-muted-foreground mt-1 tracking-wider">
          DATA SOURCE: <span className="text-bull">LIVE</span>
        </p>
      </div>
    </aside>
  );
}