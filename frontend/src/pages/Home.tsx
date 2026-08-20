import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  ShieldAlert, 
  Volume2, 
  Radio, 
  BellRing, 
  ArrowRight, 
  Sparkles, 
  CheckCircle2, 
  Flame, 
  Zap, 
  VolumeX
} from 'lucide-react';
import ScrambleText from '../components/ScrambleText';
import TiltCard from '../components/TiltCard';
import MagneticButton from '../components/MagneticButton';
import HorizontalScrollSection from '../components/HorizontalScrollSection';
import AcousticWaveform from '../components/AcousticWaveform';
import DraggableShowcase from '../components/DraggableShowcase';
import RadarScanner from '../components/RadarScanner';

const THREAT_CLASSES = [
  {
    icon: <Flame className="w-6 h-6 text-rose-400" />,
    name: "Gunshots & Explosions",
    tier: "TIER 2 CRITICAL",
    latency: "< 12 ms",
    confidence: "96.4%",
    badgeColor: "border-rose-500/30 bg-rose-500/10 text-rose-400",
    desc: "Impulsive ballistic pressure transients. Immediate native OS banner, 10s abort window, and Telegram audio proof dispatch.",
  },
  {
    icon: <BellRing className="w-6 h-6 text-rose-400" />,
    name: "Fire Alarms & Sirens",
    tier: "TIER 2 CRITICAL",
    latency: "< 14 ms",
    confidence: "94.8%",
    badgeColor: "border-rose-500/30 bg-rose-500/10 text-rose-400",
    desc: "Harmonic high-decibel safety tones. Evaluated over 5-frame rolling gate to ensure sustained physical presence.",
  },
  {
    icon: <Zap className="w-6 h-6 text-amber-400" />,
    name: "Glass Break & Smash",
    tier: "TIER 1 WARNING",
    latency: "< 9 ms",
    confidence: "89.2%",
    badgeColor: "border-amber-500/30 bg-amber-500/10 text-amber-400",
    desc: "High-frequency brittle resonance. High-priority desktop notification with refractory period lock.",
  },
  {
    icon: <Volume2 className="w-6 h-6 text-amber-400" />,
    name: "Distress Screams",
    tier: "TIER 1 WARNING",
    latency: "< 15 ms",
    confidence: "88.7%",
    badgeColor: "border-amber-500/30 bg-amber-500/10 text-amber-400",
    desc: "Vocal panic formant tracking. Differentiates human screams from ambient speech and environmental noise.",
  },
  {
    icon: <VolumeX className="w-6 h-6 text-cyan-400" />,
    name: "Speaker Media Echo",
    tier: "SUPPRESSED",
    latency: "< 3 ms",
    confidence: "99.8%",
    badgeColor: "border-cyan-500/30 bg-cyan-500/10 text-cyan-400",
    desc: "Cross-correlated against laptop loopback audio. Gunshots from YouTube videos or games are 100% neutralized.",
  },
  {
    icon: <Radio className="w-6 h-6 text-emerald-400" />,
    name: "Ambient Room Normal",
    tier: "BACKGROUND",
    latency: "< 1 ms",
    confidence: "99.9%",
    badgeColor: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
    desc: "Continuous sub-threshold monitoring with zero CPU throttle and zero battery drain.",
  },
];

export const Home: React.FC = () => {
  return (
    <div className="pt-24 pb-20 overflow-hidden">
      
      {/* 1. HERO SECTION */}
      <section className="relative min-h-[85vh] flex items-center justify-center px-4 md:px-8 py-16">
        
        {/* Dynamic Glow Orbs */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-gradient-to-tr from-emerald-500/15 via-cyan-500/10 to-violet-500/15 rounded-full blur-[140px] pointer-events-none" />

        <div className="max-w-7xl mx-auto w-full text-center relative z-10">
          
          {/* Status Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-mono mb-8 shadow-[0_0_20px_rgba(0,245,155,0.15)]"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>REAL-TIME ACOUSTIC DEFENSE // DUAL-STREAM DSP</span>
          </motion.div>

          {/* Main Title with Scramble Text Effect */}
          <motion.h1
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1, ease: "easeOut" }}
            className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black font-display tracking-tight text-white max-w-5xl mx-auto leading-[1.08] mb-6"
          >
            Autonomous <span className="gradient-text-cyber">Acoustic AI</span> For Zero-Latency Threat Defense.
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2, ease: "easeOut" }}
            className="text-slate-300 text-base sm:text-lg md:text-xl max-w-3xl mx-auto leading-relaxed mb-10 font-normal"
          >
            Echo listens at the edge with Google YAMNet, cancels speaker media echo via FFT cross-correlation, and dispatches automated Telegram emergency briefings with live GPS and audio proof.
          </motion.p>

          {/* Action CTAs with Spring Physics Magnetic Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3, ease: "easeOut" }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer">
              <MagneticButton variant="primary" className="!px-8 !py-4 !text-base">
                <span>Launch Live Mission Control</span>
                <ArrowRight className="w-4 h-4" />
              </MagneticButton>
            </a>

            <Link to="/features">
              <MagneticButton variant="secondary" className="!px-8 !py-4 !text-base">
                <span>Explore Architecture Specs</span>
              </MagneticButton>
            </Link>
          </motion.div>

          {/* Live Telemetry KPI Ticker */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-4xl mx-auto"
          >
            <div className="glass-card p-4 rounded-2xl border border-white/5 bg-black/40">
              <div className="text-[11px] font-mono text-slate-400 uppercase">Inference Latency</div>
              <div className="text-xl md:text-2xl font-bold font-mono text-emerald-400 mt-1">
                <ScrambleText text="11.4 ms" speed={30} />
              </div>
            </div>
            <div className="glass-card p-4 rounded-2xl border border-white/5 bg-black/40">
              <div className="text-[11px] font-mono text-slate-400 uppercase">Echo Cancellation</div>
              <div className="text-xl md:text-2xl font-bold font-mono text-cyan-400 mt-1">
                <ScrambleText text="99.8%" speed={30} />
              </div>
            </div>
            <div className="glass-card p-4 rounded-2xl border border-white/5 bg-black/40">
              <div className="text-[11px] font-mono text-slate-400 uppercase">YAMNet Classes</div>
              <div className="text-xl md:text-2xl font-bold font-mono text-violet-400 mt-1">
                <ScrambleText text="521 Classes" speed={30} />
              </div>
            </div>
            <div className="glass-card p-4 rounded-2xl border border-white/5 bg-black/40">
              <div className="text-[11px] font-mono text-slate-400 uppercase">Cloud Privacy</div>
              <div className="text-xl md:text-2xl font-bold font-mono text-emerald-400 mt-1">
                <ScrambleText text="100% Local" speed={30} />
              </div>
            </div>
          </motion.div>

        </div>
      </section>

      {/* 2. INTERACTIVE ACOUSTIC WAVEFORM SANDBOX */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 py-12">
        <AcousticWaveform />
      </section>

      {/* 3. HORIZONTAL SCROLL DEEP DIVE (useScroll + useTransform) */}
      <HorizontalScrollSection />

      {/* 4. 3D TILT MATRIX: THREAT CLASSIFIER GRID */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 py-20">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-mono mb-3">
            <ShieldAlert className="w-3.5 h-3.5" />
            EDGE CLASSIFICATION MATRIX
          </div>
          <h2 className="text-3xl md:text-5xl font-bold font-display text-white mb-4">
            Calibrated for <span className="gradient-text-emerald">High-Stakes Acoustic Threats</span>
          </h2>
          <p className="text-slate-400 text-sm md:text-base">
            Hover over any threat tier to test 3D perspective tilt physics and inspect live confidence ceilings.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {THREAT_CLASSES.map((item, idx) => (
            <TiltCard key={idx} maxTilt={12} className="h-full">
              <div className="glass-card p-6 md:p-8 rounded-3xl h-full border border-white/10 hover:border-emerald-500/40 bg-gradient-to-b from-[#11131e] to-[#0c0d15] flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div className="p-3 rounded-2xl bg-white/5 border border-white/10">
                      {item.icon}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-[10px] font-mono font-bold border ${item.badgeColor}`}>
                      {item.tier}
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-white mb-2 font-display">
                    {item.name}
                  </h3>

                  <p className="text-slate-400 text-xs md:text-sm leading-relaxed mb-6">
                    {item.desc}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-4 border-t border-white/10 font-mono text-xs">
                  <div className="bg-black/40 p-2 rounded-xl border border-white/5">
                    <div className="text-[10px] text-slate-500">LATENCY</div>
                    <div className="text-emerald-400 font-bold mt-0.5">{item.latency}</div>
                  </div>
                  <div className="bg-black/40 p-2 rounded-xl border border-white/5">
                    <div className="text-[10px] text-slate-500">CONFIDENCE</div>
                    <div className="text-cyan-400 font-bold mt-0.5">{item.confidence}</div>
                  </div>
                </div>

              </div>
            </TiltCard>
          ))}
        </div>
      </section>

      {/* 5. SPATIAL RADAR SCANNER & DUAL DSP INGESTION */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-4">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              DUAL HARDWARE AUDIO INGESTION
            </div>
            <h2 className="text-3xl md:text-4xl font-bold font-display text-white mb-6">
              Simultaneous Microphone & WASAPI Loopback Capture
            </h2>
            <p className="text-slate-300 text-sm md:text-base leading-relaxed mb-6">
              Echo captures physical room audio via PyAudio while simultaneously sampling the laptop speaker stream via Windows SoundCard WASAPI at 16,000 Hz.
            </p>
            
            <div className="space-y-4 font-mono text-xs text-slate-300">
              <div className="flex items-start gap-3 p-3.5 rounded-2xl bg-white/5 border border-white/10">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-white font-bold">Automatic Stream Synchronization:</span> Internal queue backlog guards auto-flush jitter to prevent cross-correlation drift.
                </div>
              </div>
              <div className="flex items-start gap-3 p-3.5 rounded-2xl bg-white/5 border border-white/10">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-white font-bold">15,600 Sample Buffer Slices:</span> Normalized 0.975-second audio chunks fed continuously to edge neural classifiers.
                </div>
              </div>
              <div className="flex items-start gap-3 p-3.5 rounded-2xl bg-white/5 border border-white/10">
                <CheckCircle2 className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-white font-bold">Frozen Threat Clip Capture:</span> Saves the exact 5.0-second incident waveform for emergency Telegram dispatch.
                </div>
              </div>
            </div>
          </div>

          <div>
            <RadarScanner />
          </div>

        </div>
      </section>

      {/* 6. NATIVE DRAG GESTURES SHOWCASE */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 py-12">
        <DraggableShowcase />
      </section>

      {/* 7. BOTTOM CALL TO ACTION BANNER */}
      <section className="max-w-7xl mx-auto px-4 md:px-8 py-16">
        <div className="relative rounded-3xl p-8 md:p-14 overflow-hidden border border-emerald-500/30 bg-gradient-to-r from-[#0d141e] via-[#0b1716] to-[#120d1c] shadow-[0_0_60px_rgba(0,245,155,0.12)]">
          
          <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-emerald-500/20 rounded-full blur-[90px] pointer-events-none" />

          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/40 bg-emerald-500/10 text-emerald-400 text-xs font-mono mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              MISSION CONTROL IS READY
            </div>
            <h2 className="text-3xl md:text-5xl font-bold font-display text-white mb-4">
              Experience Real-Time Acoustic Intelligence.
            </h2>
            <p className="text-slate-300 text-sm md:text-base leading-relaxed mb-8">
              Open the live Mission Control console to view real-time microphone RMS gauges, speaker loopback dBFS, and active agent countdowns.
            </p>
            <div className="flex flex-wrap gap-4">
              <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer">
                <MagneticButton variant="primary" className="!px-8 !py-4 !text-base">
                  <span>Open Mission Control (8000)</span>
                  <ArrowRight className="w-4 h-4" />
                </MagneticButton>
              </a>
              <Link to="/contacts">
                <MagneticButton variant="secondary" className="!px-8 !py-4 !text-base">
                  <span>Emergency Contacts</span>
                </MagneticButton>
              </Link>
            </div>
          </div>

        </div>
      </section>

    </div>
  );
};
export default Home;
