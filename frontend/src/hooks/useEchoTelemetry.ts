import { useState, useEffect, useCallback, useRef } from 'react';

export interface TelemetryPacket {
  chunk_index: number;
  timestamp: string;
  mic_enabled: boolean;
  mic_rms: number;
  spk_rms: number;
  mic_dbfs: number;
  spk_dbfs: number;
  mic_device_name: string;
  speaker_name: string;
  top_prediction: {
    class_name: string;
    confidence: number;
  };
  target_scores: Record<string, number>;
  firewall: {
    cross_correlation: number;
    is_suppressed: boolean;
    suppressed_total: number;
    confirmed_total: number;
  };
  temporal_buffer: Array<{
    slot: number;
    chunk_idx: number;
    class_name: string;
    confidence: number;
    is_target: boolean;
    is_suppressed: boolean;
  }>;
  gate_qualifying_count: number;
  alert_state: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'PAUSED';
  active_hazard: any;
  agent_state: any;
}

export function useEchoTelemetry() {
  const [telemetry, setTelemetry] = useState<TelemetryPacket | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    try {
      const wsUrl = 'ws://localhost:8000/ws';
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data: TelemetryPacket = JSON.parse(event.data);
          setTelemetry(data);
          if (typeof data.mic_enabled === 'boolean') {
            setIsPaused(!data.mic_enabled);
          }
        } catch (err) {
          console.error('Error parsing telemetry frame:', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Attempt reconnection after 2 seconds
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, 2000);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };
    } catch (e) {
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  // Toggle Microphone Stream via Backend REST API
  const toggleMic = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/toggle-mic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (typeof data.mic_enabled === 'boolean') {
        setIsPaused(!data.mic_enabled);
      }
    } catch (e) {
      console.warn('Backend not reachable, toggling UI locally:', e);
      setIsPaused((prev) => !prev);
    }
  };

  // Trigger Emergency Dispatch via Backend REST API
  const triggerEmergency = async (hazardType = 'Gunshot') => {
    try {
      const res = await fetch('http://localhost:8000/api/trigger-telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hazard_type: hazardType }),
      });
      return await res.json();
    } catch (e) {
      console.warn('Backend not reachable, simulated trigger:', e);
      return { status: 'SIMULATED', hazard_type: hazardType };
    }
  };

  return {
    telemetry,
    isConnected,
    isPaused,
    toggleMic,
    triggerEmergency,
  };
}
export default useEchoTelemetry;
