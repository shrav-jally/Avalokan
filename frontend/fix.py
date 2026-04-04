import os, re
from datetime import datetime, timezone

# Fix app.py
with open('D:/mp_Avalokan/Avalokan/backend/app.py', 'r', encoding='utf-8') as f:
    app_text = f.read()

target_app = """        # Handle date updates (optional)
        if data.get('startDate'):
            updates['startDate'] = datetime.strptime(data['startDate'], '%Y-%m-%d')
        if data.get('endDate'):
            updates['endDate'] = datetime.strptime(data['endDate'], '%Y-%m-%d')

        # Handle status toggle (open / closed)
        if 'status' in data:
            updates['status'] = data['status']"""

replacement_app = """        # Handle date updates (optional)
        if data.get('startDate'):
            try:
                updates['startDate'] = datetime.fromisoformat(data['startDate'].replace('Z', '+00:00'))
            except ValueError:
                updates['startDate'] = datetime.strptime(data['startDate'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        if data.get('endDate'):
            try:
                end_date = datetime.fromisoformat(data['endDate'].replace('Z', '+00:00'))
            except ValueError:
                end_date = datetime.strptime(data['endDate'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            updates['endDate'] = end_date
            
            # Auto-Calculate Status
            closing_boundary = end_date.replace(hour=23, minute=59, second=59, microsecond=999000)
            now = datetime.now(timezone.utc)
            if now > closing_boundary:
                updates['status'] = 'closed'
                updates['closed_at'] = now
            else:
                updates['status'] = 'open'

        # Handle status toggle (open / closed)
        if 'status' in data and not data.get('endDate'):
            updates['status'] = data['status']"""

# Normalizing carriage returns for safe replacing
app_text = app_text.replace('\r\n', '\n')
app_text = app_text.replace(target_app, replacement_app)
with open('D:/mp_Avalokan/Avalokan/backend/app.py', 'w', encoding='utf-8') as f:
    f.write(app_text)

# Fix DraftManagement.jsx
with open('D:/mp_Avalokan/Avalokan/frontend/src/components/DraftManagement.jsx', 'r', encoding='utf-8') as f:
    dm_text = f.read()

dm_text = dm_text.replace('\r\n', '\n')

target_dm = """    if (isEditing) {
      axios.put(`http://localhost:5000/api/admin/update-draft/${currentDraft.id}`, {
        startDate: formData.startDate,
        endDate: formData.endDate
      }).then((res) => {
        if (res.status === 200) {
          setDrafts(drafts.map(d => 
            d.id === currentDraft.id 
              ? { ...d, title: formData.title, startDate: formData.startDate, endDate: formData.endDate, file: formData.file || d.file } 
              : d
          ));
        }
      }).catch(err => setFormError("Failed to save dates in database."));"""

replacement_dm = """    if (isEditing) {
      const isoStart = new Date(formData.startDate).toISOString();
      const isoEnd = new Date(formData.endDate).toISOString();
      axios.put(`http://localhost:5000/api/admin/update-draft/${currentDraft.id}`, {
        startDate: isoStart,
        endDate: isoEnd
      }, { withCredentials: true }).then((res) => {
        if (res.status === 200) {
          fetchDrafts();
        }
      }).catch(err => setFormError("Failed to save dates in database."));"""

dm_text = dm_text.replace(target_dm, replacement_dm)

with open('D:/mp_Avalokan/Avalokan/frontend/src/components/DraftManagement.jsx', 'w', encoding='utf-8') as f:
    f.write(dm_text)

print('Done')
