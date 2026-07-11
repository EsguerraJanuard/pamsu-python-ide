// This page represents the main Student IDE workspace.
// It explicitly imports the Sidebar and Statusbar to form a complete layout shell.

import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Statusbar from "../components/Statusbar";

export default function Workspace() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0f1117] text-white overflow-hidden select-none cursor-default">
      {/* MAIN SPLIT: Sidebar on the left, Workspace on the right */}
      <div className="flex flex-1 overflow-hidden">

        {/* Manually added Sidebar with the activePage prop */}
        <Sidebar activePage="Workspace" />

        {/* WORKSPACE CONTENT AREA */}
        <main 
          className="flex-1 flex flex-col min-w-0 relative bg-[#0f1117]"
          style={{
            opacity: mounted ? 1 : 0,
            transform: mounted ? "translateY(0)" : "translateY(10px)",
            transition: "opacity 0.65s cubic-bezier(0.25, 0.46, 0.45, 0.94) 0.1s, transform 0.65s cubic-bezier(0.25, 0.46, 0.45, 0.94) 0.1s"
          }}
        >
          {/* TOP IDE NAVBAR */}
          <div className="h-12 flex items-center justify-between px-4 border-b border-white/[0.08] bg-[#0f1117]">
            {/* Left: Menus */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3 text-xs text-white/60">
                <span className="hover:text-white transition-colors cursor-pointer">File</span>
                <span className="hover:text-white transition-colors cursor-pointer">Edit</span>
                <span className="hover:text-white transition-colors cursor-pointer">View</span>
                <span className="hover:text-white transition-colors cursor-pointer">Run</span>
              </div>
            </div>

            {/* Center: File Path */}
            <div className="text-xs text-white/40 flex items-center gap-2">
              <span>CCS101</span> / <span>Lab Activity 3</span> / <span className="text-white">fibonacci.py</span>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/[0.04] text-[11px] text-white/50 border border-white/[0.04]">
                <div className="w-1.5 h-1.5 rounded-full bg-[#22c55e]"></div>
                23:14
              </div>
              <button type="button" className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-[#22c55e]/10 text-[#22c55e] text-xs font-semibold border border-[#22c55e]/20 hover:bg-[#22c55e]/20 transition-colors">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><path d="M5 3l14 9-14 9V3z"/></svg>
                Run
              </button>
              <button type="button" className="px-3 py-1 rounded-md bg-[#a78bfa] text-[#0f1117] text-xs font-bold hover:bg-[#8b5cf6] transition-colors">
                Submit
              </button>
              <div className="w-6 h-6 rounded-full bg-[#1a1d27] border border-white/[0.08] flex items-center justify-center text-[10px] font-bold text-[#3b82f6]">
                JD
              </div>
            </div>
          </div>

          {/* THREE-COLUMN EDITOR LAYOUT */}
          <div className="flex-1 flex overflow-hidden">
            
            {/* COLUMN 1: Problem Description */}
            <div className="w-[280px] flex flex-col border-r border-white/[0.08] bg-[#0f1117]">
              <div className="p-4 border-b border-white/[0.08] flex items-center justify-between">
                <span className="text-[10px] font-bold text-white/40 tracking-widest uppercase">Problem</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded border border-[#f59e0b]/30 text-[#f59e0b] bg-[#f59e0b]/10">Due today</span>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-6">
                <div>
                  <h2 className="text-sm font-semibold text-white mb-2">Lab Activity 3 — Fibonacci Sequence</h2>
                  <p className="text-[13px] text-white/60 leading-relaxed">
                    Write a Python program that generates the first n Fibonacci numbers.
                  </p>
                </div>
                
                <div>
                  <h3 className="text-xs font-semibold text-white/80 mb-3">Requirements</h3>
                  <p className="text-[11px] text-white/50 mb-2">Your solution must include:</p>
                  <div className="flex flex-wrap gap-2">
                    {["def function", "for loop", "while loop", "if/else", "type annotations", "list comprehension"].map(req => (
                      <span key={req} className="px-2 py-1 rounded border border-[#3b82f6]/30 text-[#60a5fa] bg-[#3b82f6]/10 text-[11px]">
                        {req}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-semibold text-white/80 mb-2">Expected output</h3>
                  <div className="p-3 rounded-lg bg-[#1a1d27] border border-white/[0.08] font-mono text-[11px] space-y-1">
                    <div className="text-[#22c55e]">Sequence: [0,1,1,2,3,5,8,13,21,34]</div>
                    <div className="text-[#22c55e]">Even: [0,2,8,34]</div>
                  </div>
                </div>
              </div>
            </div>

            {/* COLUMN 2: Editor & Terminal */}
            <div className="flex-1 flex flex-col min-w-0 bg-[#0f1117] relative">
              {/* Context Switching Warning Overlay */}
              <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#f59e0b]/10 border border-[#f59e0b]/30 text-[#f59e0b] text-[11px] backdrop-blur-sm">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                Warning: Context-switching recorded — tab switch ×3
                <button type="button" className="ml-2 hover:text-white">✕</button>
              </div>

              {/* Editor Tabs */}
              <div className="flex border-b border-white/[0.08] bg-[#0f1117]">
                <div className="flex items-center gap-2 px-4 py-2 border-t-2 border-t-[#f59e0b] bg-[#1a1d27] text-xs text-white">
                  <span className="text-[#f59e0b]">fibonacci.py</span>
                  <div className="w-1.5 h-1.5 rounded-full bg-[#f59e0b]"></div>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 text-xs text-white/40 border-t-2 border-t-transparent hover:bg-white/[0.02]">
                  <span className="text-[#3b82f6]">utils.py</span>
                </div>
              </div>

              {/* Editor Code Area */}
              <div className="flex-1 p-4 font-mono text-[13px] leading-6 select-text cursor-text overflow-y-auto">
                <div className="flex">
                  <div className="w-8 text-right pr-4 text-white/20 select-none">
                    1<br/>2<br/>3<br/>4<br/>5
                  </div>
                  <div className="flex-1 text-white/80">
                    <span className="text-white/40"># Lab Activity 3 — Fibonacci Sequence</span><br/>
                    <span className="text-white/40"># Student: Juan, Miguel D. | CCS101</span><br/>
                    <br/>
                    <span className="text-[#f59e0b]">def</span> <span className="text-[#60a5fa]">fibonacci</span>(n: <span className="text-[#38bdf8]">int</span>) -&gt; <span className="text-[#38bdf8]">list</span>[<span className="text-[#38bdf8]">int</span>]:<br/>
                    &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-[#a78bfa]">"""Return the first n Fibonacci numbers."""</span>
                  </div>
                </div>
              </div>

              {/* Terminal Panel */}
              <div className="h-[240px] flex flex-col border-t border-white/[0.08] bg-[#0f1117]">
                <div className="flex items-center border-b border-white/[0.08] px-2">
                  <div className="px-3 py-2 text-[11px] text-white border-b-2 border-white cursor-pointer flex items-center gap-1">
                    &gt;_ Terminal
                  </div>
                  <div className="px-3 py-2 text-[11px] text-white/40 hover:text-white/80 cursor-pointer flex items-center gap-1.5">
                    Problems <span className="px-1 rounded bg-[#ef4444]/20 text-[#ef4444] text-[9px]">8</span>
                  </div>
                  <div className="px-3 py-2 text-[11px] text-white/40 hover:text-white/80 cursor-pointer">
                    Output
                  </div>
                </div>
                <div className="flex-1 p-3 font-mono text-[12px] text-white/60 overflow-y-auto select-text cursor-text">
                  <div className="text-[#3b82f6] mb-1">$ python fibonacci.py</div>
                  <div className="text-[#22c55e]">Sequence: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]</div>
                  <div className="text-[#22c55e] mb-2">Even: [0, 2, 8, 34]</div>
                  <div className="text-white/30">Process finished with exit code 0 · 0.041s</div>
                  <div className="text-[#3b82f6] mt-1">$ <span className="w-1.5 h-3 bg-white/40 inline-block animate-pulse align-middle"></span></div>
                </div>
              </div>
            </div>

            {/* COLUMN 3: Code Analysis */}
            <div className="w-[280px] flex flex-col border-l border-white/[0.08] bg-[#0f1117]">
              <div className="p-4 border-b border-white/[0.08] flex items-center justify-between">
                <span className="text-[10px] font-bold text-white/40 tracking-widest uppercase">Code Analysis</span>
                <span className="text-[10px] font-mono font-bold text-[#22c55e]">87 / 100</span>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {/* Score Bars */}
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-[11px] mb-1.5">
                      <span className="text-white/60">Skills (AST)</span>
                      <span className="text-[#3b82f6] font-mono">72</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/[0.04] rounded-full overflow-hidden">
                      <div className="h-full bg-[#3b82f6]" style={{ width: "72%" }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-[11px] mb-1.5">
                      <span className="text-white/60">Behavior</span>
                      <span className="text-[#22c55e] font-mono">91</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/[0.04] rounded-full overflow-hidden">
                      <div className="h-full bg-[#22c55e]" style={{ width: "91%" }}></div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-2 rounded bg-[#3b82f6]/10 border border-[#3b82f6]/20 mt-2">
                    <span className="text-[11px] text-white/50">Level</span>
                    <span className="text-[11px] font-semibold text-[#60a5fa]">Developing</span>
                  </div>
                </div>

                {/* Structure Checks */}
                <div>
                  <h3 className="text-[10px] font-bold text-white/40 tracking-widest uppercase mb-3">Structure Checks</h3>
                  <div className="space-y-2 text-[11px]">
                    <div className="flex items-start gap-2 text-white/70">
                      <span className="text-[#22c55e] mt-0.5">✓</span> Function: <span className="font-mono text-[#f59e0b] ml-1">fibonacci()</span>
                    </div>
                    <div className="flex items-start gap-2 text-white/70">
                      <span className="text-[#22c55e] mt-0.5">✓</span> <span className="font-mono text-[#f59e0b]">for</span> loop present
                    </div>
                    <div className="p-2 rounded bg-[#ef4444]/10 border border-[#ef4444]/20 text-[#ef4444]">
                      <div className="flex items-center gap-1.5 font-semibold mb-1">
                        <span>×</span> Missing <span className="font-mono text-white/70">while</span> loop
                      </div>
                      <div className="text-[9px] text-[#ef4444]/70">Required by this task</div>
                    </div>
                  </div>
                </div>

              </div>
            </div>

          </div>
        </main>
      </div>

      {/* Imported Statusbar Component anchors to the bottom */}
      <Statusbar />
    </div>
  );
}