import React from 'react';
import { ExternalLink, Activity } from 'lucide-react';
import MagneticButton from '../components/MagneticButton';

export const DashboardLink: React.FC = () => {
  return (
    <div className="pt-32 pb-20 max-w-4xl mx-auto px-4 text-center">
      <div className="glass-card p-10 md:p-16 rounded-3xl border border-emerald-500/30 bg-gradient-to-b from-[#0e121e] to-[#080910]">
        
        <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto mb-6">
          <Activity className="w-8 h-8 text-emerald-400 animate-pulse" />
        </div>

        <h1 className="text-3xl md:text-5xl font-bold font-display text-white mb-4">
          Echo Mission Control
        </h1>

        <p className="text-slate-300 text-sm md:text-base max-w-xl mx-auto mb-8 leading-relaxed">
          The full interactive Mission Control dashboard runs on port 8000 connected directly to local hardware audio streams, WebSocket telemetry, and emergency hunt-groups.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer">
            <MagneticButton variant="primary" className="!px-8 !py-4 !text-base">
              <span>Open Mission Control (localhost:8000)</span>
              <ExternalLink className="w-4 h-4" />
            </MagneticButton>
          </a>
        </div>

      </div>
    </div>
  );
};
export default DashboardLink;
