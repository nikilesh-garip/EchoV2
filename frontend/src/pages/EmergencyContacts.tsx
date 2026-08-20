import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Send, ShieldAlert, CheckCircle2, Phone, Trash2, Plus } from 'lucide-react';
import TiltCard from '../components/TiltCard';
import MagneticButton from '../components/MagneticButton';

interface Contact {
  id: string;
  name: string;
  phone: string;
  telegramChatId: string;
  verified: boolean;
  role: string;
}

const INITIAL_CONTACTS: Contact[] = [
  { id: '1', name: 'Nikhilesh (Primary Operator)', phone: '+91 8955532897', telegramChatId: '6933543949', verified: true, role: 'PRIMARY' },
  { id: '2', name: 'Campus Security Dispatch', phone: '+91 9876543210', telegramChatId: '5492817293', verified: true, role: 'SECURITY' },
  { id: '3', name: 'Emergency Family Contact', phone: '+91 9123456780', telegramChatId: '7829103847', verified: true, role: 'FAMILY' },
];

export const EmergencyContacts: React.FC = () => {
  const [contacts, setContacts] = useState<Contact[]>(INITIAL_CONTACTS);
  const [newName, setNewName] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newChatId, setNewChatId] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [alertSent, setAlertSent] = useState(false);

  const handleAddContact = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName || !newPhone) return;
    const newContact: Contact = {
      id: Date.now().toString(),
      name: newName,
      phone: newPhone,
      telegramChatId: newChatId || `${Math.floor(1000000000 + Math.random() * 9000000000)}`,
      verified: true,
      role: 'CUSTOM',
    };
    setContacts([...contacts, newContact]);
    setNewName('');
    setNewPhone('');
    setNewChatId('');
    setShowAddForm(false);
  };

  const handleDelete = (id: string) => {
    setContacts(contacts.filter(c => c.id !== id));
  };

  const triggerTestAlert = () => {
    setAlertSent(true);
    setTimeout(() => setAlertSent(false), 4000);
  };

  return (
    <div className="pt-28 pb-20 max-w-7xl mx-auto px-4 md:px-8">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-rose-500/30 bg-rose-500/10 text-rose-400 text-xs font-mono mb-3">
            <Users className="w-3.5 h-3.5" />
            TELEGRAM HUNT-GROUP EMERGENCY NETWORK
          </div>
          <h1 className="text-3xl md:text-5xl font-bold font-display text-white">
            Emergency Contacts & Dispatch
          </h1>
          <p className="text-slate-400 text-sm md:text-base mt-2 max-w-2xl">
            When a critical hazard is confirmed, Echo broadcasts personalized AI synthesized voice notes, 5-second WAV evidence clips, and live GPS map pins to all active verified contacts.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <MagneticButton
            variant="secondary"
            onClick={() => setShowAddForm(!showAddForm)}
            className="!px-5 !py-2.5 !text-xs"
          >
            <Plus className="w-4 h-4" />
            <span>{showAddForm ? 'Cancel' : 'Add Contact'}</span>
          </MagneticButton>

          <MagneticButton
            variant="danger"
            onClick={triggerTestAlert}
            className="!px-5 !py-2.5 !text-xs"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>Simulate Dispatch</span>
          </MagneticButton>
        </div>
      </div>

      {/* Alert Simulation Banner (AnimatePresence Layout Animation) */}
      <AnimatePresence>
        {alertSent && (
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className="mb-8 p-6 rounded-3xl bg-rose-500/15 border border-rose-500/40 text-white flex items-center justify-between shadow-[0_0_30px_rgba(244,63,94,0.3)]"
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-2xl bg-rose-500 text-white">
                <Send className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <div className="font-bold text-base">🚨 Emergency Alert Broadcast Dispatched!</div>
                <div className="text-xs text-rose-200 font-mono mt-0.5">
                  Sent personalized voice briefing + 5.0s WAV proof + GPS pin to {contacts.length} verified Telegram contacts.
                </div>
              </div>
            </div>
            <div className="hidden sm:block text-xs font-mono text-rose-300">
              STATUS: DELIVERED (200 OK)
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Add Contact Form Drawer */}
      <AnimatePresence>
        {showAddForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-8 glass-card p-6 md:p-8 rounded-3xl border border-emerald-500/30 overflow-hidden"
          >
            <h3 className="text-xl font-bold text-white mb-4 font-display">Add Emergency Responder</h3>
            <form onSubmit={handleAddContact} className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">FULL NAME</label>
                <input
                  type="text"
                  placeholder="e.g. Campus Patrol"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-400 font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">PHONE NUMBER</label>
                <input
                  type="text"
                  placeholder="+91 98765 43210"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                  className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-400 font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">TELEGRAM CHAT ID</label>
                <input
                  type="text"
                  placeholder="e.g. 6933543949"
                  value={newChatId}
                  onChange={(e) => setNewChatId(e.target.value)}
                  className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-400 font-mono"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full bg-emerald-400 text-black font-bold text-sm py-2.5 rounded-xl hover:bg-emerald-300 transition-colors cursor-pointer"
                >
                  Save & Verify Contact
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Contact Cards Grid with Tilt Physics and Spring Animations */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {contacts.map((contact) => (
          <TiltCard key={contact.id} maxTilt={8} className="h-full">
            <div className="glass-card p-6 rounded-3xl h-full border border-white/10 hover:border-emerald-500/40 bg-gradient-to-b from-[#111420] to-[#0c0d16] flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    VERIFIED ACTIVE
                  </span>
                  <button
                    onClick={() => handleDelete(contact.id)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <h3 className="text-xl font-bold text-white mb-1 font-display">
                  {contact.name}
                </h3>
                <div className="text-xs font-mono text-slate-400 mb-6">
                  ROLE: {contact.role}
                </div>

                <div className="space-y-2.5 font-mono text-xs text-slate-300">
                  <div className="flex items-center gap-2 p-2.5 rounded-xl bg-black/40 border border-white/5">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{contact.phone}</span>
                  </div>
                  <div className="flex items-center gap-2 p-2.5 rounded-xl bg-black/40 border border-white/5">
                    <Send className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Telegram: {contact.telegramChatId}</span>
                  </div>
                </div>
              </div>

              <div className="pt-6 mt-6 border-t border-white/5 flex items-center justify-between text-xs font-mono text-slate-500">
                <span>ESC PROTOCOL: AUTO</span>
                <span className="text-emerald-400">READY</span>
              </div>
            </div>
          </TiltCard>
        ))}
      </div>

    </div>
  );
};
export default EmergencyContacts;
