import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Radio, Volume2, Cpu, Bot, BellRing } from 'lucide-react';
import TiltCard from './TiltCard';

interface ShowcaseCard {
  id: string;
  tag: string;
  title: string;
  description: string;
  latency: string;
  badgeColor: string;
  icon: React.ReactNode;
  metrics: { label: string; value: string }[];
}

const SHOWCASE_CARDS: ShowcaseCard[] = [
  {
    id: "yamnet",
    tag: "EDGE AI CLASSIFICATION",
    title: "Google YAMNet Edge Model",
    description: "Real-time edge inference over 521 audio classes. Detects gunshots, explosions, glass breaking, and scream acoustics in under 12ms on CPU.",
    latency: "11.4 ms",
    badgeColor: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
    icon: <Cpu className="w-8 h-8 text-emerald-400" />,
    metrics: [
      { label: "Classes Evaluated", value: "521" },
      { label: "Sample Rate", value: "16.0 kHz" },
      { label: "Confidence Floor", value: "85.0%" },
    ],
  },
  {
    id: "firewall",
    tag: "REAL-TIME ACOUSTIC FIREWALL",
    title: "Dual-Stream Echo Cancellation",
    description: "FFT cross-correlation engine separating ambient physical threats from laptop speaker playback, music, and YouTube videos to eliminate false alarms.",
    latency: "2.1 ms",
    badgeColor: "text-cyan-400 border-cyan-500/30 bg-cyan-500/10",
    icon: <Volume2 className="w-8 h-8 text-cyan-400" />,
    metrics: [
      { label: "Correlation Threshold", value: "0.35" },
      { label: "Media Suppression Rate", value: "99.8%" },
      { label: "Hardware Loopback", value: "WASAPI" },
    ],
  },
  {
    id: "temporal",
    tag: "TEMPORAL GATE VALIDATION",
    title: "5-Frame Rolling Logic Gate",
    description: "Eliminates transient mic noise spikes by requiring 3 out of 5 consecutive time frames (4.875s window) before triggering high-priority escalation.",
    latency: "0.4 ms",
    badgeColor: "text-violet-400 border-violet-500/30 bg-violet-500/10",
    icon: <Radio className="w-8 h-8 text-violet-400" />,
    metrics: [
      { label: "Sliding Window", value: "5 Frames" },
      { label: "Gate Threshold", value: "≥ 3 / 5" },
      { label: "Incident History", value: "Persistent" },
    ],
  },
  {
    id: "agent",
    tag: "ANTIGRAVITY ORCHESTRATOR",
    title: "Autonomous Security Policy Agent",
    description: "Debounces threat events with refractory periods, triggers native OS popups, and initiates a 10s Human-in-the-Loop abort window.",
    latency: "0.8 ms",
    badgeColor: "text-amber-400 border-amber-500/30 bg-amber-500/10",
    icon: <Bot className="w-8 h-8 text-amber-400" />,
    metrics: [
      { label: "Abort Countdown", value: "10.0 sec" },
      { label: "Refractory Lock", value: "45.0 sec" },
      { label: "OS Notification", value: "Native Banner" },
    ],
  },
  {
    id: "telegram",
    tag: "TELEGRAM HUNT-GROUP",
    title: "Automated Emergency Dispatch",
    description: "Broadcasts AI edge-tts voice notes, verified incident audio snippets, and Google Maps live GPS coordinates to verified emergency contacts.",
    latency: "340 ms",
    badgeColor: "text-rose-400 border-rose-500/30 bg-rose-500/10",
    icon: <BellRing className="w-8 h-8 text-rose-400" />,
    metrics: [
      { label: "Audio Proof Clip", value: "5.0s .WAV" },
      { label: "Voice Synthesis", value: "Neural Edge TTS" },
      { label: "GPS Dispatch", value: "Live Coordinate" },
    ],
  },
];

export const HorizontalScrollSection: React.FC = () => {
  const targetRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: targetRef,
    offset: ["start start", "end end"],
  });

  // Transform vertical scroll to horizontal scroll
  const x = useTransform(scrollYProgress, [0, 1], ["2%", "-72%"]);
  const progressWidth = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);
  const titleOpacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [1, 0.9, 0.9, 0.4]);

  return (
    <section ref={targetRef} className="relative h-[320vh] bg-[#07070a]">
      {/* Sticky container that stays fixed while page scrolls vertically */}
      <div className="sticky top-0 flex flex-col justify-center h-screen overflow-hidden px-4 md:px-12">
        
        {/* Section Heading & Progress Tracker */}
        <motion.div style={{ opacity: titleOpacity }} className="mb-8 max-w-7xl mx-auto w-full">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-mono mb-3">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                HORIZONTAL ARCHITECTURE DEEP DIVE
              </div>
              <h2 className="text-3xl md:text-5xl font-bold font-display tracking-tight text-white">
                Under the Hood: <span className="gradient-text-emerald">End-to-End Pipeline</span>
              </h2>
              <p className="text-slate-400 text-sm md:text-base mt-2 max-w-2xl">
                Scroll vertically to inspect each layer of the acoustic defense system running in real-time.
              </p>
            </div>

            {/* Scroll Progress Bar */}
            <div className="w-full md:w-64">
              <div className="flex justify-between text-xs font-mono text-slate-400 mb-1.5">
                <span>PIPELINE PROGRESS</span>
                <span>5 MODULES</span>
              </div>
              <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                <motion.div style={{ width: progressWidth }} className="h-full bg-gradient-to-r from-cyan-400 via-emerald-400 to-violet-400 rounded-full" />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Horizontal Card Track */}
        <motion.div style={{ x }} className="flex gap-8 pb-4 items-center">
          {SHOWCASE_CARDS.map((card, idx) => (
            <div key={card.id} className="w-[360px] md:w-[480px] shrink-0">
              <TiltCard maxTilt={10} className="h-full">
                <div className="glass-card p-8 rounded-3xl h-full flex flex-col justify-between border border-white/10 hover:border-emerald-500/40 bg-gradient-to-b from-[#11131c]/90 to-[#0c0d14]/90 relative group">
                  
                  {/* Glowing Ambient Backdrop on Card */}
                  <div className="absolute top-0 right-0 w-36 h-36 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none group-hover:bg-emerald-500/15 transition-all duration-500" />
                  
                  <div>
                    {/* Header: Tag + Icon */}
                    <div className="flex items-center justify-between mb-6">
                      <span className={`px-3 py-1 rounded-full text-xs font-mono font-medium border ${card.badgeColor}`}>
                        {card.tag}
                      </span>
                      <div className="p-3 rounded-2xl bg-white/5 border border-white/10">
                        {card.icon}
                      </div>
                    </div>

                    {/* Step Number & Title */}
                    <div className="text-xs font-mono text-slate-500 mb-1">MODULE 0{idx + 1} // LATENCY: {card.latency}</div>
                    <h3 className="text-2xl font-bold text-white mb-3 font-display group-hover:text-emerald-300 transition-colors">
                      {card.title}
                    </h3>

                    {/* Description */}
                    <p className="text-slate-300 text-sm leading-relaxed mb-6">
                      {card.description}
                    </p>
                  </div>

                  {/* Metrics Box */}
                  <div className="grid grid-cols-3 gap-2 pt-4 border-t border-white/10 font-mono">
                    {card.metrics.map((m, mIdx) => (
                      <div key={mIdx} className="bg-black/40 p-2.5 rounded-xl border border-white/5 text-center">
                        <div className="text-[10px] text-slate-400 uppercase tracking-wider">{m.label}</div>
                        <div className="text-xs md:text-sm font-bold text-emerald-400 mt-1">{m.value}</div>
                      </div>
                    ))}
                  </div>

                </div>
              </TiltCard>
            </div>
          ))}
        </motion.div>

      </div>
    </section>
  );
};
export default HorizontalScrollSection;
