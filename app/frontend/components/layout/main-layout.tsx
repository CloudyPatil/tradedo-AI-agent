// E:\tradedo\app\frontend\components\layout\main-layout.tsx

import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

interface Props {
  children: React.ReactNode;
}

export function MainLayout({ children }: Props) {
  return (
    <div className="h-screen flex overflow-hidden bg-background">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar />
        
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-border bg-card px-6 py-2 flex items-center justify-between text-[10px] text-muted-foreground font-mono">
          <div className="flex items-center gap-4">
            <span>GRID: 8PT</span>
            <span>BASELINE: 4PT</span>
            <span>ORIGIN: (0,0)</span>
          </div>
          
          <div className="tracking-wider">
            BUILT WITH <span className="text-brand font-bold">AI.</span> BACKED BY <span className="text-brand font-bold">DATA.</span>
          </div>
          
          <div className="flex items-center gap-4">
            <span>SIZE: RESPONSIVE</span>
            <span>MARGIN: 24PX</span>
          </div>
        </footer>
      </div>
    </div>
  );
}