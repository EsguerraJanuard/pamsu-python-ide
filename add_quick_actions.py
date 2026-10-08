import os
import re

filepath = "frontend/src/features/admin/AdminDashboard.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add QuickActionCard component
quick_action_component = """
function QuickActionCard({ title, desc, icon, onClick }) {
  return (
    <button onClick={onClick} className="group flex flex-col items-start p-6 rounded-2xl bg-bg-glass border border-border-subtle hover:bg-bg-panel hover:border-psu-maroon/50 dark:hover:border-psu-gold/50 hover:shadow-md transition-all text-left w-full h-full">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-bg-base border border-border-strong text-psu-maroon dark:text-psu-gold mb-4 group-hover:scale-110 group-hover:shadow-sm transition-all">
        {icon}
      </div>
      <h4 className="font-bold text-text-main text-sm mb-1">{title}</h4>
      <p className="text-xs text-text-muted">{desc}</p>
    </button>
  );
}

function Input({ label, ...props }) {"""

content = content.replace("function Input({ label, ...props }) {", quick_action_component)


# Add Quick Actions section
overview_end_target = """                  </div>
                </div>
              )}

            {activeTab === 'faculty' && ("""

quick_actions_section = """                  </div>

                  <div className="mt-10 animate-fade-in" style={{ animationDelay: '100ms' }}>
                    <h3 className="text-lg font-black mb-6 tracking-tight">Quick Actions</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      <QuickActionCard 
                         title="Provision Faculty" 
                         desc="Create a new instructor account"
                         icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg>}
                         onClick={() => handleTabChange('faculty')}
                      />
                      <QuickActionCard 
                         title="Manage Students" 
                         desc="Upload a new batch of students"
                         icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>}
                         onClick={() => handleTabChange('students')}
                      />
                      <QuickActionCard 
                         title="Audit Logs" 
                         desc="Review recent platform activity"
                         icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>}
                         onClick={() => handleTabChange('audit')}
                      />
                      <QuickActionCard 
                         title="System Settings" 
                         desc="Configure strictness and maintenance"
                         icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /></svg>}
                         onClick={() => handleTabChange('settings')}
                      />
                    </div>
                  </div>
                </div>
              )}

            {activeTab === 'faculty' && ("""

content = content.replace(overview_end_target, quick_actions_section)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Added Quick Actions")
