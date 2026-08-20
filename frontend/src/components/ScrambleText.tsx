import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface ScrambleTextProps {
  text: string;
  className?: string;
  speed?: number;
  triggerOnHover?: boolean;
}

const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";

export const ScrambleText: React.FC<ScrambleTextProps> = ({
  text,
  className = "",
  speed = 25,
  triggerOnHover = true,
}) => {
  const [displayText, setDisplayText] = useState(text);
  const [isScrambling, setIsScrambling] = useState(false);

  const startScramble = () => {
    if (isScrambling) return;
    setIsScrambling(true);
    let iteration = 0;
    const interval = setInterval(() => {
      setDisplayText(
        text
          .split("")
          .map((char, index) => {
            if (char === " ") return " ";
            if (index < iteration) {
              return text[index];
            }
            return CHARS[Math.floor(Math.random() * CHARS.length)];
          })
          .join("")
      );

      if (iteration >= text.length) {
        clearInterval(interval);
        setIsScrambling(false);
      }
      iteration += 1 / 2;
    }, speed);
  };

  useEffect(() => {
    startScramble();
  }, [text]);

  return (
    <motion.span
      className={`inline-block font-mono tracking-tight cursor-default ${className}`}
      onMouseEnter={() => {
        if (triggerOnHover) startScramble();
      }}
      whileHover={{ scale: 1.01 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      {displayText}
    </motion.span>
  );
};
export default ScrambleText;
