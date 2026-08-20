import React from 'react';
import { Cpu, ArrowUpRight } from 'lucide-react';
import TiltCard from '../components/TiltCard';

const PIPELINE_STEPS = [
  {
    step: "01",
    title: "Dual Hardware Audio Capture",
    tech: "PyAudio + SoundCard WASAPI @ 16kHz",
    desc: "Captures physical microphone audio in parallel with speaker loopback. Synchronizes sample queues to ensure zero drift.",
    badge: "15,600 SAMPLES / CHUNK",
  },
  {
    step: "02",
    title: "Edge Neural Inference",
    tech: "Google YAMNet Edge Model",
    desc: "Evaluates 521 audio classes in 11ms on device CPU. Extracts log-mel spectrogram features and computes class probabilities.",
    badge: "11.4 MS INFERENCE",
  },
  {
    step: "03",
    title: "FFT Acoustic Firewall",
    tech: "Cross-Correlation & Suppression DSP",
    desc: "Calculates normalized cross-correlation between microphone and loopback audio. Suppresses YouTube and movie sounds to zero false alarms.",
    badge: "r < 0.35 LIMIT",
  },
  {
    step: "04",
    title: "5-Frame Temporal Gate",
    tech: "Sliding Queue Validation Gate",
    desc: "Requires ≥ 3 out of 5 consecutive time slices (4.875s window) above confidence threshold before initiating threat response.",
    badge: "≥ 3 / 5 CONSECUTIVE",
  },
  {
    step: "05",
    title: "Antigravity Security Agent",
    tech: "Human-in-the-Loop Policy Engine",
    desc: "Applies 45s refractory debouncing, pops native OS banners, and launches a 10s countdown window allowing user abort.",
    badge: "10S ESCALATION WINDOW",
  },
  {
    step: "06",
    title: "Telegram Bot Hunt-Group",
    tech: "Neural Edge TTS + GPS Location",
    desc: "Dispatches personalized voice briefings, 5-second WAV evidence clips, and live GPS map pins to verified emergency contacts.",
    badge: "INSTANT BROADCAST",
  },
];

export const Features: React.FC = () => {
  return (
    <div className="pt-28 pb-20 max-w-7xl mx-auto px-4 md:px-8">
      
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-4">
          <Cpu className="w-3.5 h-3.5" />
          SYSTEM SPECIFICATIONS
        </div>
        <h1 className="text-4xl md:text-6xl font-bold font-display text-white mb-6">
          Architected for <span className="gradient-text-cyber">Zero False Positives</span>
        </h1>
        <p className="text-slate-300 text-sm md:text-base leading-relaxed">
          Explore the mathematical foundations, edge neural inference engines, and dual-stream cancellation pipelines powering Echo.
        </p>
      </div>

      {/* Grid of Architecture Pipeline Steps */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-20">
        {PIPELINE_STEPS.map((item, idx) => (
          <TiltCard key={idx} maxTilt={10} className="h-full">
            <div className="glass-card p-8 rounded-3xl h-full border border-white/10 hover:border-emerald-500/40 bg-gradient-to-b from-[#10121d] to-[#0c0e16] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-6">
                  <span className="font-mono text-2xl font-black text-emerald-400">
                    {item.step}
                  </span>
                  <span className="px-2.5 py-1 rounded-full text-[10px] font-mono border border-white/10 bg-white/5 text-slate-300">
                    {item.badge}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-2 font-display">
                  {item.title}
                </h3>
                <div className="text-xs font-mono text-emerald-400 mb-4">
                  {item.tech}
                </div>
                <p className="text-slate-400 text-xs md:text-sm leading-relaxed">
                  {item.desc}
                </p>
              </div>
              <div className="pt-6 mt-6 border-t border-white/5 flex items-center justify-between text-xs font-mono text-slate-500">
                <span>PHASE {item.step} / 06</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  VERIFIED <ArrowUpRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          </TiltCard>
        ))}
      </div>

      {/* Performance Matrix Table */}
      <div className="glass-card p-8 md:p-12 rounded-3xl border border-white/10 bg-black/40">
        <h3 className="text-2xl font-bold font-display text-white mb-6">
          Performance Benchmarks & Acoustic Bounds
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs text-slate-300">
            <thead>
              <tr className="border-b border-white/10 text-slate-500 text-[11px]">
                <th className="pb-4">SUBSYSTEM</th>
                <th className="pb-4">PROCESSING METHOD</th>
                <th className="pb-4">LATENCY</th>
                <th className="pb-4">ACCURACY / FLOOR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              <tr>
                <td className="py-4 font-bold text-white">YAMNet Neural Core</td>
                <td className="py-4">Edge TensorFlow Model on CPU</td>
                <td className="py-4 text-emerald-400">11.4 ms</td>
                <td className="py-4">85.0% Confidence Floor</td>
              </tr>
              <tr>
                <td className="py-4 font-bold text-white">Acoustic Firewall</td>
                <td className="py-4">FFT Cross-Correlation Normalized</td>
                <td className="py-4 text-cyan-400">2.1 ms</td>
                <td className="py-4">r &lt; 0.35 Rejection Boundary</td>
              </tr>
              <tr>
                <td className="py-4 font-bold text-white">Temporal Gate</td>
                <td className="py-4">5-Frame FIFO Queue Gate</td>
                <td className="py-4 text-violet-400">0.4 ms</td>
                <td className="py-4">≥ 3 / 5 Consecutive Frames</td>
              </tr>
              <tr>
                <td className="py-4 font-bold text-white">Telegram Dispatch</td>
                <td className="py-4">Edge TTS + WAV Upload + Telegram API</td>
                <td className="py-4 text-amber-400">340 ms</td>
                <td className="py-4">100% Verified Delivery</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
export default Features;
