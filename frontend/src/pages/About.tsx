import React from 'react';
import { Lock, Cpu, HeartHandshake, Sparkles } from 'lucide-react';
import TiltCard from '../components/TiltCard';

export const About: React.FC = () => {
  return (
    <div className="pt-28 pb-20 max-w-7xl mx-auto px-4 md:px-8">
      
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto mb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-300 text-xs font-mono mb-4">
          <Sparkles className="w-3.5 h-3.5" />
          THE MISSION BEHIND ECHO
        </div>
        <h1 className="text-4xl md:text-6xl font-bold font-display text-white mb-6">
          Acoustic Defense Without <span className="gradient-text-cyber">Privacy Compromise</span>
        </h1>
        <p className="text-slate-300 text-base md:text-lg leading-relaxed">
          Traditional smart assistants stream your private home audio to centralized cloud servers. Echo was born out of a single principle: real-time acoustic threat defense must happen 100% on the edge.
        </p>
      </div>

      {/* Core Principles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
        
        <TiltCard maxTilt={8} className="h-full">
          <div className="glass-card p-8 rounded-3xl h-full border border-white/10 bg-gradient-to-b from-[#111420] to-[#0c0d15] flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-6">
                <Lock className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3 font-display">100% Local Inference</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Raw audio never leaves your physical machine. TensorFlow YAMNet executes entirely in local memory with zero external cloud dependencies.
              </p>
            </div>
            <div className="pt-6 mt-6 border-t border-white/5 text-xs font-mono text-emerald-400">
              ZERO TELEMETRY LEAKAGE
            </div>
          </div>
        </TiltCard>

        <TiltCard maxTilt={8} className="h-full">
          <div className="glass-card p-8 rounded-3xl h-full border border-white/10 bg-gradient-to-b from-[#111420] to-[#0c0d15] flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-6">
                <Cpu className="w-6 h-6 text-cyan-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3 font-display">Sub-15ms Latency</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                By eliminating network roundtrips, Echo detects impulsive acoustic transients (gunshots, shatter, alarms) in under 15 milliseconds.
              </p>
            </div>
            <div className="pt-6 mt-6 border-t border-white/5 text-xs font-mono text-cyan-400">
              INSTANT RESPONSE TIME
            </div>
          </div>
        </TiltCard>

        <TiltCard maxTilt={8} className="h-full">
          <div className="glass-card p-8 rounded-3xl h-full border border-white/10 bg-gradient-to-b from-[#111420] to-[#0c0d15] flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center mb-6">
                <HeartHandshake className="w-6 h-6 text-violet-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3 font-display">Human-in-the-Loop</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Every critical escalation triggers a 10-second desktop abort window with audio preview before contacting emergency responders.
              </p>
            </div>
            <div className="pt-6 mt-6 border-t border-white/5 text-xs font-mono text-violet-400">
              OPERATOR OVERRIDE
            </div>
          </div>
        </TiltCard>

      </div>

    </div>
  );
};
export default About;
