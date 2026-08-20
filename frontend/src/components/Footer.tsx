import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Send, Lock, Code2 } from 'lucide-react';
import ScrambleText from './ScrambleText';

export const Footer: React.FC = () => {
  return (
    <footer className="relative bg-[#050608] border-t border-white/10 pt-16 pb-12 overflow-hidden">
      
      {/* Background Decorative Radial Gradient */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[200px] bg-emerald-500/5 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 md:px-8 relative z-10">
        
        {/* Top Row: Brand & Live Status Ticker */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-white/10">
          
          {/* Brand Info */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-xl bg-emerald-400/20 border border-emerald-400/40 flex items-center justify-center">
                <Shield className="w-5 h-5 text-emerald-400" />
              </div>
              <span className="font-display font-extrabold text-xl text-white tracking-wider">ECHO ACOUSTIC</span>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed max-w-md mb-6">
              Autonomous edge acoustic intelligence platform engineered for real-time sound hazard classification, dual-stream media suppression, and automated Telegram emergency dispatch.
            </p>
            <div className="flex items-center gap-3">
              <a
                href="https://github.com/nikilesh-garip/EchoV2.git"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:border-emerald-400/40 transition-colors flex items-center gap-2 text-xs font-mono"
              >
                <Code2 className="w-4 h-4 text-emerald-400" />
                <span>GitHub Repository</span>
              </a>
              <a
                href="https://t.me"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-cyan-400 hover:border-cyan-400/40 transition-colors flex items-center gap-2 text-xs font-mono"
              >
                <Send className="w-4 h-4 text-cyan-400" />
                <span>Telegram Bot</span>
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <div className="text-xs font-mono text-emerald-400 font-bold uppercase tracking-wider mb-4">
              System Modules
            </div>
            <ul className="space-y-2.5 text-xs text-slate-400 font-mono">
              <li>
                <Link to="/" className="hover:text-emerald-400 transition-colors">→ Threat Detection</Link>
              </li>
              <li>
                <Link to="/features" className="hover:text-emerald-400 transition-colors">→ Acoustic Firewall</Link>
              </li>
              <li>
                <Link to="/about" className="hover:text-emerald-400 transition-colors">→ Latency Benchmarks</Link>
              </li>
              <li>
                <Link to="/contacts" className="hover:text-emerald-400 transition-colors">→ Telegram Hunt-Group</Link>
              </li>
            </ul>
          </div>

          {/* Telemetry Status Box */}
          <div className="bg-white/5 p-4 rounded-2xl border border-white/5 font-mono text-xs">
            <div className="flex items-center justify-between mb-3 text-[11px] text-slate-400">
              <span>SECURITY AGENT</span>
              <span className="text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                ACTIVE
              </span>
            </div>
            <div className="space-y-1.5 text-slate-300 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-500">Inference Core:</span>
                <span>YAMNet (CPU)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Refractory Debounce:</span>
                <span>45.0s Lock</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Echo Correlation:</span>
                <span>r &lt; 0.35</span>
              </div>
            </div>
          </div>

        </div>

        {/* Bottom Row */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-slate-500">
          <div>
            © 2026 Echo Acoustic Intelligence. All rights reserved.
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1 text-slate-400">
              <Lock className="w-3.5 h-3.5 text-emerald-400" />
              100% On-Device DSP
            </span>
            <span>•</span>
            <span className="text-slate-400">
              Built with <ScrambleText text="Motion.dev + React" speed={30} />
            </span>
          </div>
        </div>

      </div>
    </footer>
  );
};
export default Footer;
