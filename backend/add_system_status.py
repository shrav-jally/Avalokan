import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

system_status_route = '''@app.route("/api/system/status", methods=["GET"])
def get_system_status():
    return jsonify({
        "status": "healthy",
        "models": [
            {"name": "Sentiment", "id": "distilbert-base-uncased-finetuned-sst-2-english", "v": "1.0"},
            {"name": "Toxicity", "id": "unitary/toxic-bert", "v": "1.0"},
            {"name": "Summarizer", "id": "t5-small", "v": "1.1"}
        ],
        "last_refresh": datetime.now(timezone.utc).isoformat()
    })

if __name__ == '__main__':'''

text = text.replace("if __name__ == '__main__':", system_status_route)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Added /api/system/status to app.py.")
