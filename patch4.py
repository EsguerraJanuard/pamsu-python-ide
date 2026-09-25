import re
with open('frontend/src/features/instructor/ActivityEditor.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# We need to auto-publish the task if formData.is_published is true.
# Look for: delete payload.allow_paste;
# const response = await api.post('/instructors/tasks/', payload);
# ...
# if (formData.is_published) {
#   for (const task of tasks) { await api.patch('/instructors/tasks/' + task.task_id + '/publication', { is_published: true }); }
# }

patch = '''
        const response = await api.post('/instructors/tasks/', payload);
        const tasks = Array.isArray(response) ? response : [response];
        
        if (formData.is_published) {
          for (const task of tasks) {
            try {
              await api.patch(/instructors/tasks//publication, { is_published: true });
            } catch (pubErr) {
              console.error('Failed to auto-publish task', pubErr);
            }
          }
        }
'''

c = c.replace("const response = await api.post('/instructors/tasks/', payload);", patch)
with open('frontend/src/features/instructor/ActivityEditor.jsx', 'w', encoding='utf-8') as f:
    f.write(c)