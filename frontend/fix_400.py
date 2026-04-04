import os

# Fix app.py
with open('D:/mp_Avalokan/Avalokan/backend/app.py', 'r', encoding='utf-8') as f:
    app_text = f.read()

target_app = """@app.route("/api/admin/update-draft/<draft_id>", methods=["PUT", "POST"])
def update_draft_dates(draft_id):
    try:
        data = request.json
        updates = {}

        # Handle date updates (optional)
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
            updates['endDate'] = end_date"""

replacement_app = """from dateutil import parser

@app.route("/api/admin/update-draft/<path:draft_id>", methods=["PUT", "POST"])
def update_draft_dates(draft_id):
    try:
        data = request.json
        print("Update Request Payload:", data)
        updates = {}

        # Handle date updates (optional)
        if data.get('startDate'):
            updates['startDate'] = parser.parse(data['startDate'])
            if not updates['startDate'].tzinfo:
                updates['startDate'] = updates['startDate'].replace(tzinfo=timezone.utc)
                
        if data.get('endDate'):
            end_date = parser.parse(data['endDate'])
            if not end_date.tzinfo:
                end_date = end_date.replace(tzinfo=timezone.utc)
            updates['endDate'] = end_date"""

app_text = app_text.replace('\r\n', '\n')
app_text = app_text.replace(target_app, replacement_app)

with open('D:/mp_Avalokan/Avalokan/backend/app.py', 'w', encoding='utf-8') as f:
    f.write(app_text)

# Fix DraftManagement.jsx
with open('D:/mp_Avalokan/Avalokan/frontend/src/components/DraftManagement.jsx', 'r', encoding='utf-8') as f:
    dm_text = f.read()

dm_text = dm_text.replace('\r\n', '\n')

target_dm = """    if (isEditing) {
      const isoStart = new Date(formData.startDate).toISOString();
      const isoEnd = new Date(formData.endDate).toISOString();
      axios.put(`http://localhost:5000/api/admin/update-draft/${currentDraft.id}`, {
        startDate: isoStart,
        endDate: isoEnd
      }, { withCredentials: true }).then((res) => {"""

replacement_dm = """    if (isEditing) {
      const closingBoundary = new Date(formData.endDate);
      closingBoundary.setHours(23, 59, 59, 999);
      const computedStatus = (new Date() > closingBoundary) ? 'closed' : 'open';

      const isoStart = new Date(formData.startDate).toISOString().split('T')[0];
      const isoEnd = new Date(formData.endDate).toISOString().split('T')[0];
      const safeId = encodeURIComponent(currentDraft.id);
      
      axios.put(`http://localhost:5000/api/admin/update-draft/${safeId}`, {
        startDate: isoStart,
        endDate: isoEnd,
        status: computedStatus
      }, { withCredentials: true }).then((res) => {"""

dm_text = dm_text.replace(target_dm, replacement_dm)

with open('D:/mp_Avalokan/Avalokan/frontend/src/components/DraftManagement.jsx', 'w', encoding='utf-8') as f:
    f.write(dm_text)

print('Done')
