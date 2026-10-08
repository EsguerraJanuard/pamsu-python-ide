import os
import re

filepath = "frontend/src/features/auth/Login.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

features_array = """const features = [
  {
    label: "AST-driven structural feedback",
    color: "#22c55e",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
        <path d="M5 8l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    label: "Privacy-conscious behavioral indicators",
    color: "#38bdf8",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="3" stroke="currentColor" strokeWidth="1.5" />
        <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1" strokeDasharray="2 2" />
      </svg>
    ),
  },
  {
    label: "Instructor activity monitoring",
    color: "#a855f7",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <rect x="2" y="3" width="12" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" />
        <path d="M2 7h12" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    ),
  },
  {
    label: "Jaccard similarity review indicators",
    color: "#eab308",
    icon: (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M8 2l2 4 4.5.5-3.5 3 1 4.5-4-2.5-4 2.5 1-4.5-3.5-3L6 6l2-4z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      </svg>
    ),
  },
];
"""

if "const features =" not in content:
    content = content.replace('const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";', 
                              'const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";\n\n' + features_array)

features_jsx = """          <p className="mt-6 max-w-md text-sm leading-relaxed text-white/80">
            A browser-based Python environment that supports structural feedback, safe code execution, personal practice, and instructor-guided review.
          </p>
          
          <ul className="mt-8 space-y-4">
            {features.map((feature, idx) => (
              <li key={idx} className="flex items-center gap-3 text-sm font-medium text-white/90">
                <div 
                  className="flex h-6 w-6 items-center justify-center rounded-full bg-white/10" 
                  style={{ color: feature.color }}
                >
                  {feature.icon}
                </div>
                {feature.label}
              </li>
            ))}
          </ul>"""

old_p = """          <p className="mt-6 max-w-md text-base leading-relaxed text-white/80">
            A secure, browser-based Python environment built specifically for Pampanga State University. Features automated structural feedback, telemetry monitoring, and zero-setup isolated execution.
          </p>"""

content = content.replace(old_p, features_jsx)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Restored features list with icons")
