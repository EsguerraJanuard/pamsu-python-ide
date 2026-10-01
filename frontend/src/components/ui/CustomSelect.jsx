import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../features/auth/AuthContext';

export default function CustomSelect({ options, value, onChange, placeholder = "Select an option", className = "" }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const { user } = useAuth();
  const isInstructor = user?.role === 'instructor';

  const themeColor = isInstructor ? 'emerald-500' : 'blue-500';
  const themeTextColor = isInstructor ? 'text-text-emerald' : 'text-blue-500';

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
        className={`w-full bg-bg-glass border border-border-subtle rounded-xl text-text-main focus:outline-none focus:border-${themeColor}/50 focus:ring-1 focus:ring-${themeColor}/20 transition-all group-hover:border-border-strong shadow-inner cursor-pointer flex justify-between items-center ${className || 'px-4 py-3 text-sm'}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className={selectedOption ? "text-text-main" : "text-text-muted"}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <div className={`text-text-muted transition-transform ${isOpen ? `rotate-180 ${themeTextColor}` : `group-hover:${themeTextColor}`}`}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      
      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-bg-panel border border-border-subtle rounded-xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-100">
          <ul className="max-h-60 overflow-y-auto py-1 custom-scrollbar">
            {options.map((opt) => (
              <li 
                key={opt.value}
                className={`px-4 py-3 text-sm cursor-pointer transition-colors flex items-center gap-3 ${String(value) === String(opt.value) ? `bg-${themeColor}/10 ${themeTextColor}` : 'text-text-main hover:bg-white/5 hover:text-white'}`}
                onClick={() => {
                  onChange(opt.value);
                  setIsOpen(false);
                }}
              >
                <span className={String(value) === String(opt.value) ? "font-semibold" : ""}>{opt.label}</span>
              </li>
            ))}
            {options.length === 0 && (
              <li className="px-4 py-3 text-sm text-text-muted italic text-center">
                No options available
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
