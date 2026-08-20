import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, ShieldAlert, VolumeX, Activity } from 'lucide-react';
import ScrambleText from './ScrambleText';

interface HazardSim {
  id: string;
  name: string;
  category: 'CRITICAL' | 'WARNING' | 'SUPPRESSED' | 'NORMAL';
  confidence: number;
  correlation: number;
  isSuppressed: boolean;
  classTag: string;
  color: string;
  description: string;
}

const SIM_PRESETS: HazardSim[] = [
  {
    id: 'gunshot',
    name: 'Gunshot / Weapon Discharge',
    category: 'CRITICAL',
    confidence: 0.96,
    correlation: 0.04,
    isSuppressed: false,
    classTag: 'Gunshot, gunfire (428)',
    color: '#ff3366',
    description: 'High-energy acoustic impulse. Acoustic firewall validates physical ambient origin (0.04 corr). Initiates 10s critical escalation.',
  },
  {
    id: 'fire_alarm',
    name: 'Industrial Fire Alarm Bell',
    category: 'CRITICAL',
    confidence: 0.94,
    correlation: 0.02,
    isSuppressed: false,
    classTag: 'Fire alarm (394)',
    color: '#ff3366',
    description: 'Harmonic 3.1kHz repetitive tone. Temporal gate captures 5/5 qualifying frames. Dispatches Telegram voice note and GPS alert.',
  },
  {
    id: 'glass',
    name: 'Glass Window Shatter',
    category: 'WARNING',
    confidence: 0.88,
    correlation: 0.06,
    isSuppressed: false,
    classTag: 'Shatter, smash (437)',
    color: '#ffb800',
    description: 'High-frequency brittle fracture transient. Triggers Tier-1 high-priority native OS desktop alert.',
  },
  {
    id: 'youtube_music',
    name: 'Action Movie / YouTube Video (Speaker Echo)',
    category: 'SUPPRESSED',
    confidence: 0.92,
    correlation: 0.86,
    isSuppressed: true,
    classTag: 'Explosion / Media Playback',
    color: '#00e5ff',
    description: 'Dual-stream acoustic firewall matches speaker loopback (0.86 corr). Threat safely SUPPRESSED to zero false positives.',
  },
  {
    id: 'ambient',
    name: 'Ambient Conversation & Room Noise',
    category: 'NORMAL',
    confidence: 0.12,
    correlation: 0.01,
    isSuppressed: false,
    classTag: 'Speech, room ambient (001)',
    color: '#00f59b',
    description: 'Normal background room acoustics. Temporal buffer rests in NORMAL monitoring state.',
  },
];

export const AcousticWaveform: React.FC = () => {
  const [activeSim, setActiveSim] = useState<HazardSim>(SIM_PRESETS[0]);
  const [bars, setBars] = useState<number[]>(Array.from({ length: 48 }, () => 15));
  const [gateSlots, setGateSlots] = useState<boolean[]>([true, true, true, false, true]);

  // Animate dynamic waveform bars
  useEffect(() => {
    const interval = setInterval(() => {
      setBars((prev) =>
        prev.map((_, idx) => {
          if (activeSim.category === 'CRITICAL') {
            return Math.min(100, Math.max(20, Math.sin(idx * 0.4 + Date.now() * 0.008) * 45 + 50 + (Math.random() * 20 - 10)));
          } else if (activeSim.category === 'SUPPRESSED') {
            return Math.min(80, Math.max(15, Math.cos(idx * 0.3 + Date.now() * 0.005) * 30 + 35));
          } else if (activeSim.category === 'WARNING') {
            return Math.min(85, Math.max(18, Math.sin(idx * 0.5 + Date.now() * 0.006) * 35 + 40));
          } else {
            return Math.min(30, Math.max(8, Math.sin(idx * 0.2 + Date.now() * 0.002) * 10 + 15));
          }
        })
      );
    }, 60);
    return () => clearInterval(interval);
  }, [activeSim]);

  const handleSimSelect = (sim: HazardSim) => {
    setActiveSim(sim);
    if (sim.category === 'CRITICAL') {
      setGateSlots([true, true, true, true, true]);
    } else if (sim.category === 'WARNING') {
      setGateSlots([true, true, true, false, false]);
    } else if (sim.category === 'SUPPRESSED') {
      setGateSlots([false, false, false, false, false]);
    } else {
      setGateSlots([false, false, false, false, false]);
    }
  };

  return (
    <div className="glass-card p-6 md:p-10 rounded-3xl border border-white/10 relative overflow-hidden bg-gradient-to-b from-[#0f111a]/95 to-[#090a10]/95">
      
      {/* Background Neon Accent Glow */}
      <div 
        className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-40 rounded-full blur-[100px] pointer-events-none transition-colors duration-500"
        style={{ background: activeSim.isSuppressed ? 'rgba(0, 229, 255, 0.15)' : activeSim.color + '20' }}
      />

      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-black/40 text-xs font-mono text-slate-300 mb-2">
            <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            INTERACTIVE ACOUSTIC SANDBOX
          </div>
          <h3 className="text-2xl md:text-3xl font-bold font-display text-white">
            Live Waveform & AI Defense Engine
          </h3>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-3">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSim.id}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className={`px-4 py-2 rounded-2xl font-mono text-xs font-bold border flex items-center gap-2 ${
                activeSim.isSuppressed
                  ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300 shadow-[0_0_20px_rgba(0,229,255,0.2)]'
                  : activeSim.category === 'CRITICAL'
                  ? 'border-rose-500/40 bg-rose-500/10 text-rose-400 shadow-[0_0_20px_rgba(244,63,94,0.3)]'
                  : activeSim.category === 'WARNING'
                  ? 'border-amber-500/40 bg-amber-500/10 text-amber-400 shadow-[0_0_20px_rgba(245,158,11,0.2)]'
                  : 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400 shadow-[0_0_20px_rgba(0,245,155,0.2)]'
              }`}
            >
              {activeSim.isSuppressed ? (
                <>
                  <VolumeX className="w-4 h-4 text-cyan-400" />
                  <span>ECHO FIREWALL SUPPRESSED</span>
                </>
              ) : activeSim.category === 'CRITICAL' ? (
                <>
                  <ShieldAlert className="w-4 h-4 text-rose-500 animate-bounce" />
                  <span>CRITICAL THREAT DETECTED</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>ROOM CLEAR / NORMAL</span>
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Real-time Oscilloscope & Waveform Visualizer */}
      <div className="relative h-44 md:h-52 bg-black/60 rounded-2xl border border-white/10 p-4 flex items-end justify-between gap-1 overflow-hidden mb-8">
        
        {/* Grid and Frequency Markings */}
        <div className="absolute inset-0 bg-grid opacity-30 pointer-events-none" />
        <div className="absolute top-3 left-4 text-[10px] font-mono text-slate-500">
          CH 1: PY_AUDIO 16.0 kHz // DUAL-CHANNEL DSP
        </div>
        <div className="absolute top-3 right-4 text-[10px] font-mono text-emerald-400 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          DSP ONLINE
        </div>

        {/* Dynamic Waveform Bars with Spring Layout Animations */}
        {bars.map((height, i) => (
          <motion.div
            key={i}
            animate={{ height: `${height}%` }}
            transition={{ type: "spring", stiffness: 350, damping: 20 }}
            className="w-full rounded-t-sm"
            style={{
              background: activeSim.isSuppressed
                ? `linear-gradient(to top, #00e5ff ${height * 0.8}%, #8b5cf6)`
                : `linear-gradient(to top, ${activeSim.color} ${height * 0.7}%, #ffffff)`,
              opacity: 0.75 + (height / 400),
            }}
          />
        ))}
      </div>

      {/* Telemetry Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        
        {/* YAMNet Confidence */}
        <div className="bg-white/5 p-4 rounded-2xl border border-white/5">
          <div className="text-xs font-mono text-slate-400 mb-1">YAMNET CLASSIFIER</div>
          <div className="text-lg font-bold text-white font-mono flex items-center justify-between">
            <ScrambleText text={`${(activeSim.confidence * 100).toFixed(1)}%`} speed={20} />
            <span className="text-xs text-slate-500">thresh 85%</span>
          </div>
          <div className="h-1.5 w-full bg-white/10 rounded-full mt-2 overflow-hidden">
            <motion.div
              animate={{ width: `${activeSim.confidence * 100}%` }}
              className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full"
            />
          </div>
        </div>

        {/* Firewall Cross-Correlation */}
        <div className="bg-white/5 p-4 rounded-2xl border border-white/5">
          <div className="text-xs font-mono text-slate-400 mb-1">FIREWALL CORRELATION</div>
          <div className="text-lg font-bold text-white font-mono flex items-center justify-between">
            <ScrambleText text={`r = ${activeSim.correlation.toFixed(2)}`} speed={20} />
            <span className="text-xs text-slate-500">limit 0.35</span>
          </div>
          <div className="h-1.5 w-full bg-white/10 rounded-full mt-2 overflow-hidden">
            <motion.div
              animate={{ width: `${Math.min(100, activeSim.correlation * 100)}%` }}
              className={`h-full rounded-full ${activeSim.isSuppressed ? 'bg-cyan-400' : 'bg-emerald-400'}`}
            />
          </div>
        </div>

        {/* 5-Frame Rolling Temporal Gate */}
        <div className="bg-white/5 p-4 rounded-2xl border border-white/5 md:col-span-2">
          <div className="text-xs font-mono text-slate-400 mb-2 flex justify-between">
            <span>5-FRAME TEMPORAL VALIDATION GATE</span>
            <span className="text-emerald-400 font-bold">REQ ≥ 3/5</span>
          </div>
          <div className="grid grid-cols-5 gap-2">
            {gateSlots.map((filled, idx) => (
              <motion.div
                key={idx}
                animate={{
                  backgroundColor: filled ? (activeSim.isSuppressed ? '#00e5ff' : activeSim.color) : 'rgba(255,255,255,0.05)',
                  borderColor: filled ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.1)',
                }}
                className="h-7 rounded-lg border flex items-center justify-center font-mono text-[10px] font-bold text-black"
              >
                {filled ? `F0${idx + 1}` : '-'}
              </motion.div>
            ))}
          </div>
        </div>

      </div>

      {/* Preset Selector Buttons (Interactive Sound Board) */}
      <div>
        <div className="text-xs font-mono text-slate-400 mb-3 uppercase tracking-wider">
          Simulate Ambient Acoustic Hazard Scenarios:
        </div>
        <div className="flex flex-wrap gap-2.5">
          {SIM_PRESETS.map((sim) => (
            <button
              key={sim.id}
              onClick={() => handleSimSelect(sim)}
              className={`px-4 py-2.5 rounded-xl text-xs md:text-sm font-medium transition-all duration-200 cursor-pointer border ${
                activeSim.id === sim.id
                  ? 'bg-white text-black font-bold border-white shadow-[0_0_20px_rgba(255,255,255,0.3)] scale-[1.02]'
                  : 'bg-white/5 text-slate-300 hover:text-white border-white/10 hover:border-white/30 hover:bg-white/10'
              }`}
            >
              {sim.name}
            </button>
          ))}
        </div>

        {/* Scenario Explanation */}
        <div className="mt-4 p-4 rounded-xl bg-black/40 border border-white/5 text-xs text-slate-300 font-mono">
          <span className="text-emerald-400 font-bold">INSIGHT:</span> {activeSim.description}
        </div>
      </div>

    </div>
  );
};
export default AcousticWaveform;
