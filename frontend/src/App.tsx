import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Features from './pages/Features';
import About from './pages/About';
import EmergencyContacts from './pages/EmergencyContacts';
import DashboardLink from './pages/DashboardLink';

export const App: React.FC = () => {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-[#07070a] text-white selection:bg-emerald-500 selection:text-black">
      {/* Floating Glassmorphic Navbar */}
      <Navbar />

      {/* Main Page Routes with AnimatePresence Exit Animations */}
      <main className="flex-grow">
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Home />} />
            <Route path="/features" element={<Features />} />
            <Route path="/about" element={<About />} />
            <Route path="/contacts" element={<EmergencyContacts />} />
            <Route path="/dashboard" element={<DashboardLink />} />
            <Route path="*" element={<Home />} />
          </Routes>
        </AnimatePresence>
      </main>

      {/* Futuristic Cyber Footer */}
      <Footer />
    </div>
  );
};
export default App;
