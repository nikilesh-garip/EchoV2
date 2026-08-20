import React, { useRef } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

interface MagneticButtonProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  pullStrength?: number;
}

export const MagneticButton: React.FC<MagneticButtonProps> = ({
  children,
  className = "",
  onClick,
  variant = 'primary',
  pullStrength = 0.35,
}) => {
  const btnRef = useRef<HTMLButtonElement>(null);

  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const springConfig = { damping: 15, stiffness: 200, mass: 0.1 };
  const springX = useSpring(x, springConfig);
  const springY = useSpring(y, springConfig);

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!btnRef.current) return;
    const { left, top, width, height } = btnRef.current.getBoundingClientRect();
    const centerX = left + width / 2;
    const centerY = top + height / 2;
    x.set((e.clientX - centerX) * pullStrength);
    y.set((e.clientY - centerY) * pullStrength);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return 'bg-emerald-400 text-black font-semibold shadow-[0_0_25px_rgba(0,245,155,0.4)] hover:shadow-[0_0_35px_rgba(0,245,155,0.7)]';
      case 'secondary':
        return 'bg-[#141724] text-white border border-[rgba(255,255,255,0.12)] hover:border-emerald-400/50 hover:bg-[#1a1e30]';
      case 'danger':
        return 'bg-rose-500 text-white font-semibold shadow-[0_0_25px_rgba(244,63,94,0.4)] hover:shadow-[0_0_35px_rgba(244,63,94,0.7)]';
      case 'ghost':
        return 'bg-transparent text-slate-300 hover:text-white border border-transparent hover:border-white/10';
      default:
        return 'bg-emerald-400 text-black';
    }
  };

  return (
    <motion.button
      ref={btnRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{ x: springX, y: springY }}
      whileTap={{ scale: 0.94 }}
      className={`relative inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-full transition-colors duration-200 cursor-pointer select-none text-sm tracking-wide ${getVariantStyles()} ${className}`}
    >
      {children}
    </motion.button>
  );
};
export default MagneticButton;
