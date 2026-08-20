import React, { useRef } from 'react';
import { motion } from 'framer-motion';
import { Shield, Sparkles, Zap, Smartphone, Headphones, Wifi } from 'lucide-react';
import TiltCard from './TiltCard';

interface FeatureCard {
  icon: React.ReactNode;
  title: string;
  category: string;
  tagline: string;
  badge: string;
}

const CAROUSEL_ITEMS: FeatureCard[] = [
  {
    icon: <Zap className="w-6 h-6 text-emerald-400" />,
    title: "11ms Edge YAMNet Neural Classifier",
    category: "ZERO CLOUD LATENCY",
    tagline: "Runs completely locally on device CPU without streaming private room audio to external servers.",
    badge: "100% PRIVATE",
  },
  {
    icon: <Headphones className="w-6 h-6 text-cyan-400" />,
    title: "FFT Cross-Correlation Firewall",
    category: "MEDIA SUPPRESSION",
    tagline: "Eliminates music and video echo false alarms by phase-correlating speaker output against room microphones.",
    badge: "PATENT PENDING",
  },
  {
    icon: <Shield className="w-6 h-6 text-violet-400" />,
    title: "5-Frame Temporal Rolling Gate",
    category: "FALSE ALARM IMMUNITY",
    tagline: "Requires persistent acoustic energy across consecutive chunks before escalating threats.",
    badge: "MIL-SPEC DSP",
  },
  {
    icon: <Smartphone className="w-6 h-6 text-rose-400" />,
    title: "Telegram Bot Hunt-Group Dispatch",
    category: "CRITICAL ESCALATION",
    tagline: "Sends instant AI synthesized voice briefings, 5-second WAV evidence clips, and live GPS map pins to emergency contacts.",
    badge: "MULTI-USER DB",
  },
  {
    icon: <Wifi className="w-6 h-6 text-amber-400" />,
    title: "Real-Time WebSocket Mission Control",
    category: "TELEMETRY ENGINE",
    tagline: "Broadcasts live microphone RMS, loopback dBFS, and active agent countdowns to connected dashboards at 60 FPS.",
    badge: "SUB-MILLISECOND",
  },
];

export const DraggableShowcase: React.FC = () => {
  const constraintsRef = useRef<HTMLDivElement>(null);

  return (
    <div className="relative py-12 overflow-hidden">
      
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8 px-4 md:px-0">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-300 text-xs font-mono mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            NATIVE DRAG GESTURES // SPRING MOMENTUM
          </div>
          <h2 className="text-3xl md:text-4xl font-bold font-display text-white">
            Engineered for <span className="gradient-text-cyber">Uncompromising Reliability</span>
          </h2>
        </div>
        <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
          <span>← DRAG OR SWIPE WITH TOUCH / MOUSE →</span>
        </div>
      </div>

      {/* Draggable Carousel Track */}
      <div ref={constraintsRef} className="cursor-grab active:cursor-grabbing">
        <motion.div
          drag="x"
          dragConstraints={{ right: 0, left: -680 }}
          dragElastic={0.15}
          dragTransition={{ bounceStiffness: 400, bounceDamping: 25 }}
          className="flex gap-6 pb-6 pt-2"
        >
          {CAROUSEL_ITEMS.map((item, idx) => (
            <motion.div
              key={idx}
              className="w-[310px] md:w-[360px] shrink-0 select-none"
              whileHover={{ y: -6 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
            >
              <TiltCard maxTilt={8} className="h-full">
                <div className="glass-card p-6 md:p-8 rounded-3xl h-full border border-white/10 hover:border-white/25 flex flex-col justify-between bg-gradient-to-b from-[#121522] to-[#0c0d16]">
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <div className="p-3 rounded-2xl bg-white/5 border border-white/10">
                        {item.icon}
                      </div>
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold border border-white/10 bg-white/5 text-slate-300">
                        {item.badge}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-emerald-400 mb-1.5 uppercase tracking-wider">
                      {item.category}
                    </div>
                    <h3 className="text-xl font-bold text-white mb-3 font-display">
                      {item.title}
                    </h3>
                    <p className="text-slate-400 text-xs md:text-sm leading-relaxed">
                      {item.tagline}
                    </p>
                  </div>
                  <div className="pt-6 mt-6 border-t border-white/5 flex items-center justify-between text-xs font-mono text-slate-500">
                    <span>SPEC 0{idx + 1}</span>
                    <span className="text-emerald-400 hover:underline">EXPLORE DOCS →</span>
                  </div>
                </div>
              </TiltCard>
            </motion.div>
          ))}
        </motion.div>
      </div>

    </div>
  );
};
export default DraggableShowcase;
