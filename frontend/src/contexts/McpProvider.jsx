import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import mcpService from '../services/mcpService';
import { Wifi, WifiOff } from 'lucide-react';

const McpContext = createContext(null);

export const useMcp = () => useContext(McpContext);

export const McpProvider = ({ children }) => {
  const [status, setStatus] = useState(mcpService.status);
  const hasConnected = useRef(false);

  useEffect(() => {
    if (!hasConnected.current) {
      mcpService.connect();
      hasConnected.current = true;
    }
    
    const unsubscribe = mcpService.onStatusChange(newStatus => {
      setStatus(newStatus);
    });

    return () => unsubscribe();
  }, []);

  const renderOverlay = () => {
    if (status === 'connected') return null;

    const messages = {
      connecting: 'Menghubungkan ke MCP Server...',
      disconnected: 'Koneksi ke server terputus.',
    };
    
    const Icon = status === 'connecting' ? Wifi : WifiOff;

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        <div className="flex flex-col items-center text-center p-4">
          <Icon className={`h-12 w-12 text-brand-blue mb-4 ${status === 'connecting' ? 'animate-pulse' : ''}`} />
          <p className="text-lg font-semibold text-text-primary">
            {messages[status]}
          </p>
          <p className="text-sm text-text-secondary mt-1">
            Harap tunggu atau coba refresh halaman jika masalah berlanjut.
          </p>
        </div>
      </div>
    );
  };
  
  const value = {
    service: mcpService,
    status,
  };

  return (
    <McpContext.Provider value={value}>
      {renderOverlay()}
      {children}
    </McpContext.Provider>
  );
};