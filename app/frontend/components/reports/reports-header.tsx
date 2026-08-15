// E:\tradedo\app\frontend\components\reports\reports-header.tsx

"use client";

import { FileText, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export function ReportsHeader() {
  const handleDownloadAll = () => {
    toast.info("PDF export coming soon!");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold flex items-center gap-2">
            <FileText className="text-brand" size={24} />
            REPORTS & INSIGHTS
          </h1>
          <p className="text-xs text-muted-foreground tracking-wider mt-1">
            PERFORMANCE REPORTS · TRADE JOURNAL · AI INSIGHTS
          </p>
        </div>

        <Button onClick={handleDownloadAll} className="bg-brand hover:bg-brand-500">
          <Download size={14} className="mr-2" />
          EXPORT ALL
        </Button>
      </div>
    </div>
  );
}