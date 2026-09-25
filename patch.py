import re
with open('frontend/src/components/modals/JoinClassModal.jsx', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('onSuccess(res.data.class_id)', 'onSuccess(res.class_id)')
with open('frontend/src/components/modals/JoinClassModal.jsx', 'w', encoding='utf-8') as f:
    f.write(c)