const fs = require('fs');

let backend = fs.readFileSync('backend/app/services/classroom_service.py', 'utf8');
backend = backend.replace('f"{user.first_name} {user.last_name}"', 'f"{user.last_name}, {user.first_name}"');
fs.writeFileSync('backend/app/services/classroom_service.py', backend);

let roster = fs.readFileSync('frontend/src/features/dashboard/ClassRosterView.jsx', 'utf8');
roster = roster.replace('{student?.first_name} {student?.last_name}', '{student?.name}');
fs.writeFileSync('frontend/src/features/dashboard/ClassRosterView.jsx', roster);

let modal = fs.readFileSync('frontend/src/components/modals/StudentGradebookModal.jsx', 'utf8');
modal = modal.replace('{student?.first_name} {student?.last_name}', '{student?.name}');

const html_to_inject = `<p className="text-sm text-text-muted">{student?.school_id || 'ID Unknown'} • {student?.email}</p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Global Integrity Score:</span>
                  <span className={\`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-bold ring-1 ring-inset \${
                    (student?.academic_integrity_score ?? 100) >= 90 ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20" : 
                    (student?.academic_integrity_score ?? 100) >= 70 ? "bg-amber-500/10 text-amber-400 ring-amber-500/20" : 
                    "bg-rose-500/10 text-rose-400 ring-rose-500/20"
                  }\`}>
                    {Math.round(student?.academic_integrity_score ?? 100)}%
                  </span>
                </div>`;

modal = modal.replace(/<p className="text-sm text-text-muted">\{student\?\.school_id \|\| 'ID Unknown'\} . \{student\?\.email\}<\/p>/, html_to_inject);
fs.writeFileSync('frontend/src/components/modals/StudentGradebookModal.jsx', modal);
console.log('Done');
