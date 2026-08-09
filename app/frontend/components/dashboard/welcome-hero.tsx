// E:\tradedo\app\frontend\components\dashboard\welcome-hero.tsx

export function WelcomeHero() {
  return (
    <div className="bg-card border border-border rounded-lg p-8 corner-brackets relative overflow-hidden">
      {/* Background grid */}
      <div className="absolute inset-0 grid-overlay pointer-events-none" />
      
      <div className="relative z-10">
        <h2 className="text-4xl font-display font-bold mb-1 leading-none">
          WELCOME TO
        </h2>
        <h1 className="text-5xl font-display font-black text-brand mb-6 leading-none tracking-tight">
          TRADEDO
        </h1>
        
        <div className="space-y-1 mb-6">
          <p className="text-lg font-display font-bold tracking-wider">
            AI. PREDICT.
          </p>
          <p className="text-lg font-display font-bold tracking-wider">
            TRADE. AUTOMATE.
          </p>
        </div>
        
        <div className="w-24 h-0.5 bg-brand mb-6" />
        
        <div className="space-y-1 text-sm text-muted-foreground">
          <p>Autonomous trading agent.</p>
          <p>Real-time data. AI insights.</p>
          <p>Smarter trades.</p>
          <p>Better returns.</p>
        </div>
      </div>
    </div>
  );
}