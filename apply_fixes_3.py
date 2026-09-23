import re

filepath = 'frontend/src/features/instructor/grading/GradingClassView.jsx'
with open(filepath, 'r', encoding='utf-8') as f: content = f.read()

old_card = """<div 
                key={activity.task_id} 
                className="p-6 bg-bg-glass border border-border-subtle rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-border-hover transition-colors"
              >
                <div>
                  <h3 className="text-lg font-medium text-text-main">{activity.title}</h3>
                  <p className="text-sm text-text-muted mt-1">{activity.description || 'No description provided'}</p>
                  {activity.due_date && (
                    <p className="text-xs text-text-muted mt-2">Due: {new Date(activity.due_date).toLocaleDateString()}</p>
                  )}
                </div>
                <button
                  onClick={() => navigate(`/instructor/bench/${classId}/${activity.task_id}`)}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md text-sm font-medium transition-colors whitespace-nowrap flex items-center"
                >
                  View details
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>"""

new_card = """<div 
                key={activity.task_id} 
                onClick={() => navigate(`/instructor/bench/${classId}/${activity.task_id}`)}
                className="p-6 bg-bg-glass border border-border-subtle rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-emerald-500/50 hover:shadow-lg cursor-pointer transition-all group relative overflow-hidden"
              >
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-transparent group-hover:bg-emerald-500 transition-colors"></div>
                <div>
                  <h3 className="text-lg font-bold text-text-main group-hover:text-emerald-400 transition-colors">{activity.title}</h3>
                  <p className="text-sm text-text-muted mt-1">{activity.description || 'No description provided'}</p>
                  {activity.due_date && (
                    <p className="text-xs text-text-muted mt-2 font-mono">
                      Due: {new Date(activity.due_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
                <div className="w-full sm:w-auto z-10">
                  <button 
                    className="w-full sm:w-auto rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-2 text-sm font-semibold transition group-hover:bg-emerald-600 group-hover:text-white group-hover:border-transparent group-hover:shadow-lg group-hover:shadow-emerald-500/20 flex items-center"
                  >
                    View details
                    <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>"""
content = content.replace(old_card, new_card)

with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
