import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_route = '''@app.route("/api/home/notifications", methods=["GET"])
def get_home_notifications():
    # Return a few recent comments and newly created policies as "notifications"
    recent_comments = list(comments_col.find().sort("created_at", -1).limit(3))
    recent_policies = list(policies_col.find().sort("created_at", -1).limit(2))
    
    notifications = []
    for c in recent_comments:
        notifications.append({
            "type": "comment",
            "title": f"New Comment on {c.get('draft_id', 'Draft')}",
            "message": c.get('summary', c.get('text', ''))[:100],
            "timestamp": "Recent",
            "class": "dot-new" if c.get('sentiment') == 'POSITIVE' else ("dot-urgent" if c.get('sentiment') == 'NEGATIVE' else "dot-normal")
        })
        
    for p in recent_policies:
        notifications.append({
            "type": "policy",
            "title": "New Policy Created",
            "message": f"The policy '{p.get('title')}' was successfully added to the system.",
            "timestamp": "New",
            "class": "dot-new"
        })
        
    return jsonify(notifications)

if __name__ == '__main__':'''

text = text.replace("if __name__ == '__main__':", new_route)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated app.py with /api/home/notifications.")
