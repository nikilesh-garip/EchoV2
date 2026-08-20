import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radio, AlertTriangle } from 'lucide-react';

interface ThreatBlip {
  id: string;
  name: string;
  angle: number;
  distance: number;
  tier: 'CRITICAL' | 'WARNING';
  dbfs: number;
}

const THREAT_BLIPS: ThreatBlip[] = [
  { id: '1', name: 'Gunshot Transient', angle: 45, distance: 70, tier: 'CRITICAL', dbfs: -4.2 },
  { id: '2', name: 'Fire Alarm Tone', angle: 160, distance: 85, tier: 'CRITICAL', dbfs: -6.8 },
  { id: '3', name: 'Glass Shatter', angle: 280, distance: 55, tier: 'WARNING', dbfs: -12.4 },
  { id: '4', name: 'Scream Signature', angle: 210, distance: 65, tier: 'WARNING', dbfs: -9.1 },
];

export const RadarScanner: React.FC = () => {
  const [selectedBlip, setSelectedBlip] = useState<ThreatBlip | null>(THREAT_BLIPS[0]);

  return (
    <div className="glass-card p-6 md:p-8 rounded-3xl border border-white/10 relative overflow-hidden bg-[#090b12]">
      
      {/* Background Radial Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,245,155,0.08)_0%,transparent_70%)] pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 mb-1">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            360° ACOUSTIC RADAR MAPPING
          </div>
          <h4 className="text-xl font-bold font-display text-white">Spatial Threat Localization</h4>
        </div>
        <div className="px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-mono">
          SCANNING // 16kHz
        </div>
      </div>

      {/* Radar Display Container */}
      <div className="relative w-full aspect-square max-w-[340px] mx-auto rounded-full border border-emerald-500/20 bg-black/60 p-4 flex items-center justify-center overflow-hidden shadow-[inset_0_0_40px_rgba(0,245,155,0.1)]">
        
        {/* Concentric Radar Rings */}
        <div className="absolute w-[80%] h-[80%] rounded-full border border-emerald-500/15" />
        <div className="absolute w-[60%] h-[60%] rounded-full border border-emerald-500/15" />
        <div className="absolute w-[40%] h-[40%] rounded-full border border-emerald-500/15" />
        <div className="absolute w-[20%] h-[20%] rounded-full border border-emerald-500/25" />

        {/* Crosshair Lines */}
        <div className="absolute w-full h-[1px] bg-emerald-500/15" />
        <div className="absolute h-full w-[1px] bg-emerald-500/15" />

        {/* Radar Rotating Sweep Line */}
        <div 
          className="absolute inset-0 rounded-full pointer-events-none animate-radar-sweep"
          style={{
            background: 'conic-gradient(from 0deg, rgba(0,245,155,0.4) 0deg, rgba(0,245,155,0.05) 45deg, transparent 90deg)',
          }}
        />

        {/* Threat Blip Markers */}
        {THREAT_BLIPS.map((blip) => {
          const rad = (blip.angle * Math.PI) / 180;
          const x = Math.cos(rad) * (blip.distance * 1.3);
          const y = Math.sin(rad) * (blip.distance * 1.3);

          return (
            <motion.div
              key={blip.id}
              onClick={() => setSelectedBlip(blip)}
              className="absolute z-20 cursor-pointer"
              style={{
                transform: `translate(${x}px, ${y}px)`,
              }}
              whileHover={{ scale: 1.4 }}
              whileTap={{ scale: 0.9 }}
            >
              {/* Outer Pulse */}
              <div 
                className={`w-3.5 h-3.5 rounded-full animate-ping-slow absolute -inset-0.5 ${
                  blip.tier === 'CRITICAL' ? 'bg-rose-500' : 'bg-amber-400'
                }`}
              />
              {/* Core Dot */}
              <div 
                className={`relative w-3.5 h-3.5 rounded-full border-2 border-white ${
                  blip.tier === 'CRITICAL' ? 'bg-rose-500 shadow-[0_0_12px_#ff3366]' : 'bg-amber-400 shadow-[0_0_12px_#ffb800]'
                }`}
              />
            </motion.div>
          );
        })}

        {/* Center Microphone Origin */}
        <div className="relative z-10 w-4 h-4 rounded-full bg-emerald-400 border-2 border-black flex items-center justify-center shadow-[0_0_15px_#00f59b]">
          <div className="w-1.5 h-1.5 rounded-full bg-black" />
        </div>

      </div>

      {/* Selected Threat Blip Card (Animated Layout) */}
      <AnimatePresence mode="wait">
        {selectedBlip && (
          <motion.div
            key={selectedBlip.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-6 p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between text-xs font-mono"
          >
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-xl ${selectedBlip.tier === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-400/20 text-amber-400'}`}>
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <div className="text-white font-bold">{selectedBlip.name}</div>
                <div className="text-slate-400 text-[10px]">Bearing: {selectedBlip.angle}° // Range: {selectedBlip.distance}m</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-emerald-400 font-bold">{selectedBlip.dbfs} dBFS</div>
              <div className="text-slate-500 text-[10px]">{selectedBlip.tier}</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};
export default RadarScanner;
