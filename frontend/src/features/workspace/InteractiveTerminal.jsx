import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from '@xterm/addon-fit';
import 'xterm/css/xterm.css';

const InteractiveTerminal = ({ code, onRunFinished, triggerRun }) => {
  const terminalRef = useRef(null);
  const termInstance = useRef(null);
  const wsInstance = useRef(null);
  const fitAddon = useRef(null);
  
  useEffect(() => {
    // Initialize xterm
    const term = new Terminal({
      theme: {
        background: '#0f1117',
        foreground: '#34d399',
        cursor: '#34d399'
      },
      fontFamily: 'monospace',
      cursorBlink: true,
      disableStdin: false,
    });
    
    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(terminalRef.current);
    fit.fit();
    
    termInstance.current = term;
    fitAddon.current = fit;
    
    const handleResize = () => fit.fit();
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      term.dispose();
      if (wsInstance.current) {
        wsInstance.current.close();
      }
    };
  }, []);
  
  useEffect(() => {
    if (triggerRun > 0 && code) {
      // Start run
      termInstance.current.clear();
      termInstance.current.writeln('\x1b[33m--- Starting Execution ---\x1b[0m');
      
      // Close existing ws if any
      if (wsInstance.current) {
        wsInstance.current.close();
      }
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = import.meta.env.VITE_API_BASE_URL ? new URL(import.meta.env.VITE_API_BASE_URL).host : (window.location.port === '5173' ? 'localhost:8000' : window.location.host);
      const baseUrl = import.meta.env.VITE_WS_BASE_URL || protocol + '//' + host;
      
      const ws = new WebSocket(baseUrl + '/ws/execute');
      wsInstance.current = ws;
      
      ws.onopen = () => {
        // Send code
        ws.send(code);
      };
      
      ws.onmessage = (event) => {
        // Handle incoming data
        termInstance.current.write(event.data);
      };
      
      ws.onclose = () => {
        if (onRunFinished) onRunFinished();
      };
      
      // Handle user typing
      const dataListener = termInstance.current.onData((data) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data);
        }
      });
      
      return () => {
        dataListener.dispose();
      };
    }
  }, [triggerRun, code]);

  return (
    <div className="w-full h-full p-2 bg-[#0f1117] rounded overflow-hidden relative">
      <div ref={terminalRef} className="absolute inset-2" />
    </div>
  );
};

export default InteractiveTerminal;