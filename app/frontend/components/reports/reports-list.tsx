// E:\tradedo\app\frontend\components\reports\reports-list.tsx

"use client";

import { FileText, Download, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import Link from "next/link";

const REPORTS = [
  {
    title: "Daily Trading Report",
    description: "Today's trades, P&L, and performance summary",
    icon: "📊",
    action: "view",
    href: "#daily-report",
  },
  {
    title: "Trade Journal",
    description: "Complete history with entry/exit reasoning",
    icon: "📓",
    action: "navigate",
    href: "/trades",
  },
  {
    title: "Performance Analytics",
    description: "Sharpe, Sortino, drawdown, and pro metrics",
    icon: "📈",
    action: "navigate",
    href: "/analytics",
  },
  {
    title: "Risk Assessment",
    description: "VaR, stress tests, concentration analysis",
    icon: "🛡️",
    action: "navigate",
    href: "/risk",
  },
  {
    title: "AI Insights",
    description: "Pattern discoveries and recommendations",
    icon: "🧠",
    action: "view",
    href: "#insights",
  },
  {
    title: "Sector Performance",
    description: "Win rates and P&L by sector",
    icon: "🏢",
    action: "download",
  },
  {
    title: "Monthly Summary",
    description: "Complete monthly trading report (PDF)",
    icon: "📅",
    action: "download",
  },
  {
    title: "Tax Report",
    description: "STCG/LTCG calculations for filing",
    icon: "💰",
    action: "download",
  },
];

export function ReportsList() {
  const handleDownload = (title: string) => {
    toast.info(`${title} download coming soon!`);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center gap-2 mb-4">
        <FileText size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">AVAILABLE REPORTS</h3>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {REPORTS.map((report) => (
          <div
            key={report.title}
            className="p-4 rounded-lg border border-border hover:border-brand/50 transition-all group"
          >
            <div className="flex items-start gap-3">
              <div className="text-2xl">{report.icon}</div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-bold mb-1">{report.title}</h4>
                <p className="text-[10px] text-muted-foreground mb-3">
                  {report.description}
                </p>
                
                {report.action === "navigate" && report.href ? (
                  <Link href={report.href}>
                    <Button variant="outline" size="sm" className="w-full text-[10px]">
                      <ExternalLink size={10} className="mr-1" />
                      OPEN
                    </Button>
                  </Link>
                ) : report.action === "download" ? (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full text-[10px]"
                    onClick={() => handleDownload(report.title)}
                  >
                    <Download size={10} className="mr-1" />
                    DOWNLOAD
                  </Button>
                ) : (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full text-[10px]"
                    onClick={() => {
                      const el = document.querySelector(report.href || "");
                      el?.scrollIntoView({ behavior: "smooth" });
                    }}
                  >
                    <ExternalLink size={10} className="mr-1" />
                    VIEW BELOW
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}