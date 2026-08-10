import React, { useState, useRef, useEffect } from 'react';

export default function CustomSelect({ options, value, onChange, placeholder = "Select an option" }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectedOption = options.find(opt => String(opt.value) === String(value));

  return (
    <div className="relative group" ref={dropdownRef}>
      <div 
        className="w-full bg-black/40 border border-white/[0.06] rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition-all group-hover:border-white/[0.15] shadow-inner cursor-pointer flex justify-between items-center"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className={selectedOption ? "text-white" : "text-white/50"}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <div className={`text-white/30 transition-transform ${isOpen ? 'rotate-180 text-emerald-400' : 'group-hover:text-emerald-400'}`}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      
      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-[#1a1d27] border border-white/[0.08] rounded-xl shadow-xl shadow-black/50 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
          <ul className="max-h-60 overflow-y-auto py-1 custom-scrollbar">
            {options.map((opt) => (
              <li 
                key={opt.value}
                className={`px-4 py-3 text-sm cursor-pointer transition-colors flex items-center gap-3 ${String(value) === String(opt.value) ? 'bg-emerald-500/10 text-emerald-400' : 'text-white/80 hover:bg-white/5 hover:text-white'}`}
                onClick={() => {
                  onChange(opt.value);
                  setIsOpen(false);
                }}
              >
                <div className="w-4 h-4 flex-shrink-0 flex items-center justify-center">
                  {String(value) === String(opt.value) && (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
                <span className={String(value) === String(opt.value) ? "font-semibold" : ""}>{opt.label}</span>
              </li>
            ))}
            {options.length === 0 && (
              <li className="px-4 py-3 text-sm text-white/50 italic text-center">
                No options available
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
