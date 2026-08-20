import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Radio, Activity, ExternalLink, Menu, X, Users, Info, Layers, Mic, MicOff } from 'lucide-react';
import MagneticButton from './MagneticButton';
import { useEchoTelemetry } from '../hooks/useEchoTelemetry';

const NAV_LINKS = [
  { path: '/', label: 'Overview', icon: <Radio className="w-4 h-4" /> },
  { path: '/features', label: 'AI Architecture', icon: <Layers className="w-4 h-4" /> },
  { path: '/about', label: 'About Echo', icon: <Info className="w-4 h-4" /> },
  { path: '/contacts', label: 'Emergency Network', icon: <Users className="w-4 h-4" /> },
];

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isConnected, isPaused, toggleMic } = useEchoTelemetry();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 px-4 md:px-8 pt-4 transition-all duration-300">
      <nav
        className={`max-w-7xl mx-auto rounded-full px-4 md:px-6 py-3 transition-all duration-300 flex items-center justify-between ${
          isScrolled
            ? 'glass-nav bg-[#07070acc] border border-white/10 shadow-[0_10px_30px_rgba(0,0,0,0.8)] backdrop-blur-xl'
            : 'bg-[#0a0b1280] border border-white/5 backdrop-blur-md'
        }`}
      >
        {/* Brand Logo with Glowing Pulse */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-400 to-cyan-500 p-[1px] shadow-[0_0_20px_rgba(0,245,155,0.3)] group-hover:shadow-[0_0_30px_rgba(0,245,155,0.6)] transition-shadow">
            <div className="w-full h-full bg-[#07070a] rounded-[15px] flex items-center justify-center">
              <Shield className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display font-extrabold text-lg tracking-wider text-white">ECHO</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">v2.4</span>
            </div>
            <div className="text-[9px] font-mono text-slate-400 tracking-tight hidden sm:block">
              ACOUSTIC INTELLIGENCE ENGINE
            </div>
          </div>
        </Link>

        {/* Desktop Navigation Links with Animated LayoutId Pill */}
        <div className="hidden md:flex items-center gap-1 bg-black/40 p-1.5 rounded-full border border-white/5">
          {NAV_LINKS.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`relative px-4 py-2 rounded-full text-xs font-medium transition-colors duration-200 flex items-center gap-2 ${
                  isActive ? 'text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeNavPill"
                    className="absolute inset-0 rounded-full bg-white/10 border border-white/15 shadow-[0_0_15px_rgba(255,255,255,0.05)]"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}
                <span className="relative z-10">{link.icon}</span>
                <span className="relative z-10">{link.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Action Buttons: Live Dashboard Bridge & Mic Toggle */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={toggleMic}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full border text-[11px] font-mono transition-all cursor-pointer ${
              isConnected
                ? isPaused
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20'
                  : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                : 'bg-slate-500/10 border-slate-500/20 text-slate-400'
            }`}
            title="Click to toggle microphone state"
          >
            {isConnected ? (
              isPaused ? (
                <>
                  <MicOff className="w-3.5 h-3.5 text-amber-400" />
                  <span>MIC PAUSED</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  <Mic className="w-3.5 h-3.5 text-emerald-400" />
                  <span>DSP LIVE</span>
                </>
              )
            ) : (
              <>
                <Activity className="w-3.5 h-3.5 text-slate-400" />
                <span>STANDBY</span>
              </>
            )}
          </button>

          <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer">
            <MagneticButton variant="primary" className="!px-4 !py-2 !text-xs">
              <span>Mission Control</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </MagneticButton>
          </a>
        </div>

        {/* Mobile Menu Toggle Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-xl bg-white/5 border border-white/10 text-slate-300"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </nav>

      {/* Mobile Drawer Navigation with AnimatePresence */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            className="md:hidden mt-3 p-6 rounded-3xl glass-card border border-white/10 bg-[#0a0b12f5] backdrop-blur-2xl shadow-2xl"
          >
            <div className="flex flex-col gap-3">
              {NAV_LINKS.map((link) => {
                const isActive = location.pathname === link.path;
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 p-3 rounded-2xl text-sm font-medium transition-all ${
                      isActive ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-slate-300 hover:bg-white/5'
                    }`}
                  >
                    {link.icon}
                    <span>{link.label}</span>
                  </Link>
                );
              })}
              
              <div className="pt-4 mt-2 border-t border-white/10 flex flex-col gap-3">
                <button
                  onClick={toggleMic}
                  className="w-full py-2.5 rounded-2xl bg-white/5 border border-white/10 text-xs font-mono text-white flex items-center justify-center gap-2"
                >
                  {isPaused ? <MicOff className="w-4 h-4 text-amber-400" /> : <Mic className="w-4 h-4 text-emerald-400" />}
                  <span>{isPaused ? 'Resume Mic Capture' : 'Pause Mic Capture'}</span>
                </button>

                <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer" onClick={() => setMobileMenuOpen(false)}>
                  <button className="w-full py-3 rounded-2xl bg-emerald-400 text-black font-bold text-sm flex items-center justify-center gap-2">
                    <span>Open Mission Control (8000)</span>
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </a>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};
export default Navbar;
